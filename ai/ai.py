import math
from pathlib import Path
import sys
import time

from actuators.pca9685 import Actuators, steer_to_us
from ai.infer import AiModel
from config import Config
from sensors.ld06 import LD06
from utils import angle_in_sector, clamp, polar_to_xy


def _min_front(scan, cfg: Config) -> float:
    front_vals = []
    for ang, dist in scan:
        if dist <= 0:
            continue
        if dist < cfg.dist_min_m or dist > cfg.dist_max_m:
            continue
        if not angle_in_sector(ang, cfg.front_sector_deg):
            continue
        x, _y = polar_to_xy(ang, dist)
        if x < cfg.front_x_min_m:
            continue
        front_vals.append(dist)
    if len(front_vals) < cfg.front_min_points:
        return float("nan")
    front_vals.sort()
    idx = int((cfg.front_percentile / 100.0) * (len(front_vals) - 1))
    idx = max(0, min(idx, len(front_vals) - 1))
    return front_vals[idx]


def _throttle_from_steer(cfg: Config, steer: float, min_front: float) -> float:
    throttle = cfg.throttle_base - cfg.throttle_steer_penalty * (abs(steer) ** cfg.throttle_curve_exp)
    if not math.isnan(min_front) and min_front < cfg.front_turn_on_m:
        span = max(1e-6, cfg.front_turn_on_m)
        factor = max(0.0, min(1.0, (cfg.front_turn_on_m - min_front) / span))
        throttle -= cfg.throttle_front_penalty * factor
    return clamp(throttle, cfg.throttle_min, cfg.throttle_max)


def main() -> int:
    cfg = Config()
    model_dir = Path("ai_out")
    model_path = model_dir / "model.onnx"
    stats_path = model_dir / "stats.json"
    if not model_path.exists() or not stats_path.exists():
        raise RuntimeError("Missing ai_out/model.onnx or ai_out/stats.json")

    model = AiModel(model_path, stats_path)
    lidar = LD06(cfg.lidar_port, cfg.lidar_baud, offset_deg=cfg.angle_offset_deg)
    act = Actuators(
        pca9685_address=cfg.pca9685_address,
        pca9685_freq_hz=cfg.pca9685_freq_hz,
        servo_channel=cfg.servo_channel,
        esc_channel=cfg.esc_channel,
        servo_center_us=cfg.servo_center_us,
        esc_neutral_us=cfg.esc_neutral_us,
    )
    act.stop()

    period = 1.0 / cfg.control_hz
    last_stat_t = time.time()
    last_scan_t = time.time()
    n = 0
    try:
        while True:
            t0 = time.time()
            scan = lidar.read_scan()
            if scan:
                last_scan_t = t0

            scan_age = t0 - last_scan_t
            if scan_age > cfg.lidar_timeout_s:
                steer = 0.0
                throttle = 0.0
            else:
                steer = model.predict_steer(scan)
                min_front = _min_front(scan, cfg)
                if not math.isnan(min_front) and min_front < cfg.emergency_front_m:
                    throttle = 0.0
                else:
                    throttle = _throttle_from_steer(cfg, steer, min_front)

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

            n += 1
            now = time.time()
            if now - last_stat_t >= 1.0:
                hz = n / (now - last_stat_t)
                print(f"hz={hz:.1f} steer={steer:.2f} thr={throttle:.2f} scan_age={scan_age:.2f}")
                n = 0
                last_stat_t = now

            dt = time.time() - t0
            sleep_t = period - dt
            if sleep_t > 0:
                time.sleep(sleep_t)
    except KeyboardInterrupt:
        pass
    finally:
        act.stop()
        lidar.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
