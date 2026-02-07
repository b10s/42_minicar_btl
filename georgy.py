import busio
import board
import math
from adafruit_pca9685 import PCA9685
from ld06 import LD06
from algo import calculatesteer

def us_to_duty_cycle(us, freq_hz):
    period_us = 1_000_000 / freq_hz
    duty = int(us / period_us * 65535) 
    return min(max(0, duty), 65535)

class Config:
    servo_center_us = 1480
    servo_right_us = 1720
    servo_left_us = 1240
    
    esc_neutral_us = 1450
    esc_min_us: int = 1240
    esc_max_us: int = 1720

    servo_channel = 0
    esc_channel = 1
    pca9685_address = 0x40
    pca9685_freq_hz = 58
    max_steer_deg = 15

    control_cycles = 5


class Actuators:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c, address=cfg.pca9685_address)
        self.pca.frequency = cfg.pca9685_freq_hz

    def set_servo_us(self, us: int):
        duty = us_to_duty_cycle(us, self.cfg.pca9685_freq_hz)
        self.pca.channels[self.cfg.servo_channel].duty_cycle = duty

    def set_servo_deg(self, deg: float):
        s = deg / self.cfg.max_steer_deg
        us = steer_to_us(self.cfg, s)
        print(s)
        self.set_servo_us(us)

    def set_esc_us(self, us: int):
        duty = us_to_duty_cycle(us, self.cfg.pca9685_freq_hz)
        self.pca.channels[self.cfg.esc_channel].duty_cycle = duty

    def stop(self):
        self.set_esc_us(self.cfg.esc_neutral_us)
        self.set_servo_us(self.cfg.servo_center_us)


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def steer_to_us(cfg, s):
    s = clamp(s, -1, 1)
    if s >= 0:
        return int(cfg.servo_center_us + s * (cfg.servo_right_us - cfg.servo_center_us))
    return int(cfg.servo_center_us + s * (cfg.servo_center_us - cfg.servo_left_us))

import time

if __name__ == "__main__":
    cfg = Config()
    act = Actuators(cfg)
    lidar = LD06("/dev/ttyS0", 230400)
    act.stop()

    try:
        prev = time.time()
        while True:
            for i in range(-150, 150, 5):
                time.sleep(0.1)
                print(i)
                act.set_servo_deg(i/10)
            for i in range(150, -150, -5):
                time.sleep(0.1)
                print(i)
                act.set_servo_deg(i/10)
        #act.stop()
        #exit()
        while True:
            
            scan = lidar.read_scan()
            steer = calculatesteer(scan)
            
            if time.time() - prev > cfg.control_cycles / cfg.pca9685_freq_hz:
                #print(steer)
                act.set_esc_us(1439)
                prev = time.time()
                act.set_servo_deg(-steer)

    except KeyboardInterrupt:
        pass
    finally:
        act.stop()
