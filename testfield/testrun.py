import time
import math

from config import Config
from ld06 import LD06
from pca9685 import Actuators


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def throttle_to_us(cfg: Config, throttle: float) -> int:
    throttle = clamp(throttle, 0.0, 1.0)
    return int(cfg.esc_neutral_us + throttle * (cfg.esc_max_us - cfg.esc_neutral_us))


def steer_to_us(cfg: Config, steer: float) -> int:
    steer = clamp(steer, -1.0, 1.0)
    if steer >= 0:
        return int(cfg.servo_center_us + steer * (cfg.servo_right_us - cfg.servo_center_us))
    return int(cfg.servo_center_us + steer * (cfg.servo_center_us - cfg.servo_left_us))


def angle_in_sector(deg: float, sector: tuple[float, float]) -> bool:
    a, b = sector
    deg = deg % 360.0
    a = a % 360.0
    b = b % 360.0
    if a <= b:
        return a <= deg <= b
    return deg >= a or deg <= b


def min_front_distance(
    scan_polar: list[tuple[float, float]],
    front_sector: tuple[float, float] = (350.0, 10.0),
    dist_min_m: float = 0.05,
    dist_max_m: float = 2.0,
) -> float:
    vals = []
    for ang, dist in scan_polar:
        if dist < dist_min_m or dist > dist_max_m:
            continue
        if angle_in_sector(ang, front_sector):
            print(ang, dist)
            vals.append(dist)
    return sum(vals) / len(vals) if vals else float("nan")


if __name__ == "__main__":
    cfg = Config()

    forward_throttle = -0.15  # -0.07
    obstacle_m = 1.20  # 0.70
    left_turn_steer = 1.00
    front_sector = (269.0, 271.0)  # getattr(cfg, "right_sector_deg", (350.0, 10.0))

    lidar = LD06(cfg.lidar_port, cfg.lidar_baud)
    act = Actuators(cfg)

    act.stop()
    time.sleep(0.5)
    act.set_esc_us(steer_to_us(cfg, -0.075))
    time.sleep(0.5)

    last_print = 0.0
    loop_hz = 20.0
    period = 1.0 / loop_hz

    print("Ready...")
    try:
        while True:
            t0 = time.time()

            scan = lidar.read_scan()
            mf = min_front_distance(scan, front_sector=front_sector)
            if math.isnan(mf):
                continue

            obstacle = (not math.isnan(mf)) and (mf < obstacle_m)

            if obstacle:
                steer = left_turn_steer
            else:
                steer = 0.0

            esc_us = steer_to_us(cfg, forward_throttle)
            servo_us = steer_to_us(cfg, steer)

            act.set_esc_us(esc_us)
            act.set_servo_us(servo_us)

            #if t0 - last_print > 0.1:
            print(f"min_front={mf:.3f} m  obstacle={obstacle}  steer={steer:+.2f}  esc_us={esc_us}  servo_us={servo_us}")
            #    last_print = t0

            dt = time.time() - t0
            sleep_t = period - dt
            if sleep_t > 0:
                time.sleep(sleep_t)
    except Exception as exc:
        print(exc)
    finally:
        act.stop()
        lidar.close()
