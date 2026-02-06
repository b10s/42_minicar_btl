import board
import busio
from adafruit_pca9685 import PCA9685
from config import Config
from pca9685 import Actuators
import serial
import time
import math
from ld06 import LD06
from algo import calculatesteer

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def steer_to_us(cfg, s):
    s = clamp(s, -1, 1)
    if s >= 0:
        return int(cfg.servo_center_us + s * (cfg.servo_right_us - cfg.servo_center_us))
    return int(cfg.servo_center_us + s * (cfg.servo_center_us - cfg.servo_left_us))

if __name__ == "__main__":
    cfg = Config()
    act = Actuators(cfg)
    lidar = LD06("/dev/ttyS0", 230400)
    act.stop()

    try:
        while True:
            scan = lidar.read_scan()
            act.set_esc_us(steer_to_us(cfg, -0.075))
            steer = calculatesteer(scan)
            print(steer)
            act.set_servo_us(steer_to_us(cfg, steer))

    except KeyboardInterrupt:
        pass
    finally:
        act.stop()
