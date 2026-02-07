import json
import sys
import time

from evdev import ecodes

from actuators.pca9685 import Actuators, steer_to_us
from config import Config
from sensors.ld06 import LD06
from sensors.imu_icm20948 import IMU
from tools.control import (
    _find_device,
    _norm_abs,
    ABS_X,
    ABS_Z,
    ABS_RZ,
)
from utils import clamp


def _open_device(dev_path: str | None):
    dev = _find_device(dev_path)
    if dev is None:
        raise RuntimeError("DualSense not found. Provide /dev/input/eventX as arg.")
    print(f"Using input device: {dev.path} ({dev.name})")
    try:
        dev.set_nonblocking(True)
    except Exception:
        pass
    return dev


def _init_imu(cfg: Config):
    try:
        imu = IMU(yaw_sign=cfg.imu_yaw_sign, gyro_units=cfg.imu_gyro_units)
        print("IMU initialized")
        return imu
    except Exception:
        print("IMU init failed -> running without IMU")
        return None


def _init_actuators(cfg: Config) -> Actuators:
    act = Actuators(
        pca9685_address=cfg.pca9685_address,
        pca9685_freq_hz=cfg.pca9685_freq_hz,
        servo_channel=cfg.servo_channel,
        esc_channel=cfg.esc_channel,
        servo_center_us=cfg.servo_center_us,
        esc_neutral_us=cfg.esc_neutral_us,
    )
    act.stop()
    return act


def _apply_controls(cfg: Config, act: Actuators, steer: float, throttle: float):
    steering_us = steer_to_us(
        cfg.steer_sign * steer,
        cfg.servo_center_us,
        cfg.servo_left_us,
        cfg.servo_right_us,
    )
    esc_us = steer_to_us(
        cfg.esc_forward_sign * throttle,
        cfg.esc_neutral_us,
        cfg.esc_min_us,
        cfg.esc_max_us,
    )
    act.set_servo_us(steering_us)
    act.set_esc_us(esc_us)
    return steering_us, esc_us


def _update_controls(dev, steer, throttle, r2, l2, deadzone, max_throttle):
    while True:
        event = dev.read_one()
        if event is None:
            break
        if event.type != ecodes.EV_ABS:
            continue
        if event.code == ABS_X:
            x = _norm_abs(dev, event.code, event.value) * 2.0 - 1.0
            steer = 0.0 if abs(x) < deadzone else x
        elif event.code == ABS_RZ or event.code == 5:
            r2 = _norm_abs(dev, event.code, event.value)
            throttle = clamp(r2 - l2, -max_throttle, max_throttle)
        elif event.code == ABS_Z or event.code == 2:
            l2 = _norm_abs(dev, event.code, event.value)
            throttle = clamp(r2 - l2, -max_throttle, max_throttle)
    return steer, throttle, r2, l2


def _log_row(f, row):
    f.write(json.dumps(row, separators=(",", ":")) + "\n")


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "drive_log.jsonl"
    dev_path = sys.argv[2] if len(sys.argv) > 2 else None

    cfg = Config()
    dev = _open_device(dev_path)
    lidar = LD06(cfg.lidar_port, cfg.lidar_baud, offset_deg=cfg.angle_offset_deg)
    imu = _init_imu(cfg)
    imu_retry_s = 2.0
    last_imu_retry = time.time()
    act = _init_actuators(cfg)

    steer = 0.0
    throttle = 0.0
    r2 = 0.0
    l2 = 0.0
    deadzone = 0.05
    max_throttle = cfg.throttle_max

    period = 1.0 / cfg.control_hz
    n = 0
    last_log = time.time()

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            while True:
                t0 = time.time()

                steer, throttle, r2, l2 = _update_controls(
                    dev, steer, throttle, r2, l2, deadzone, max_throttle
                )

                scan = lidar.read_scan()
                if scan:
                    now = time.time()
                    if imu is None and (now - last_imu_retry) >= imu_retry_s:
                        imu = _init_imu(cfg)
                        last_imu_retry = now
                    if imu is not None:
                        try:
                            imu_data = imu.read()
                        except Exception:
                            imu = None
                            imu_data = None
                            last_imu_retry = now
                            print("IMU read failed -> disabling IMU")
                    else:
                        imu_data = None

                    steering_us, esc_us = _apply_controls(cfg, act, steer, throttle)

                    row = {
                        "t": t0,
                        "scan": scan,
                        "steer": steer,
                        "throttle": throttle,
                        "steer_us": steering_us,
                        "esc_us": esc_us,
                    }
                    if imu_data is not None:
                        row["imu"] = imu_data
                    _log_row(f, row)
                    n += 1

                    if t0 - last_log >= 2.0:
                        hz = n / (t0 - last_log)
                        print(f"hz={hz:.1f} scans={n} out={out_path}")
                        n = 0
                        last_log = t0

                dt = time.time() - t0
                sleep_t = period - dt
                if sleep_t > 0:
                    time.sleep(sleep_t)
    except KeyboardInterrupt:
        pass
    finally:
        act.stop()
        lidar.close()


if __name__ == "__main__":
    main()
