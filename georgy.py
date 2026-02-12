import busio
import board
import time
import numpy as np
from adafruit_pca9685 import PCA9685
from ld06 import LD06
from algo import calculatesteer

def us_to_duty_cycle(us, freq_hz):
    period_us = 1_000_000 / freq_hz
    duty = int(us / period_us * 65535) 
    return min(max(0, duty), 65535)

class Config:
    servo_center_us = 1470
    servo_right_us = 1760
    servo_left_us = 1270
    
    esc_neutral_us = 1500
    esc_min_us: int = 1000
    esc_max_us: int = 2000

    servo_channel = 1
    esc_channel = 0
    pca9685_address = 0x40
    pca9685_freq_hz = 58
    max_steer_deg = 15
    steer_sign = -1

    control_cycles = 5


class Actuators:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c, address=cfg.pca9685_address)
        self.pca.frequency = cfg.pca9685_freq_hz
        self.stop()

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

if __name__ == "__main__":
    def controlsteer(prev, curr, new):
        overhit = 1.5
        if abs(curr - prev) > abs(new - curr):
            return new
        else: 
            luft = 0
            if np.sign(curr - prev) != np.sign(new - curr):
                luft = 1
            return curr + (new - curr) * overhit + np.sign((new - curr)) * luft
    cfg = Config()
    act = Actuators(cfg)
    lidar = LD06("/dev/ttyS0", 230400)
    try:
        input("Press Enter to drive...")
        print("Driving.")
        act.set_esc_us(1479)
                
        prevtime = time.time()
        prevsteer = 0.0
        currsteer = 0.0
        newsteer = 0.0
        while True:
            scan = lidar.read_scan()
            prev_steer = currsteer 
            currsteer = calculatesteer(scan)
            newsteer = controlsteer(prevsteer, currsteer, newsteer)
            now = time.time()
            dt = cfg.control_cycles / cfg.pca9685_freq_hz
            if now - prevtime > dt:    
                prevtime = now
                act.set_servo_deg(cfg.steer_sign * newsteer)
    except KeyboardInterrupt:
        pass
    finally:
        act.stop()
