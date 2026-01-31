import board
import busio
from adafruit_pca9685 import PCA9685

from config import Config


def us_to_duty_cycle(us: int, freq_hz: int) -> int:
    period_us = 1_000_000.0 / freq_hz
    duty = int((us / period_us) * 65535)
    return min(max(0, duty), 65535)


class Actuators:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c, address=cfg.pca9685_address)
        self.pca.frequency = cfg.pca9685_freq_hz

    def set_servo_us(self, us: int):
        duty = us_to_duty_cycle(us, self.cfg.pca9685_freq_hz)
        self.pca.channels[self.cfg.servo_channel].duty_cycle = duty

    def set_esc_us(self, us: int):
        duty = us_to_duty_cycle(us, self.cfg.pca9685_freq_hz)
        self.pca.channels[self.cfg.esc_channel].duty_cycle = duty

    def stop(self):
        self.set_esc_us(self.cfg.esc_neutral_us)
        self.set_servo_us(self.cfg.servo_center_us)


if __name__ == "__main__":
    import time

    def exai(cfg: Config, skorost: int):
        if skorost == 1:
            act.set_esc_us(steer_to_us(cfg, -0.1))
        if skorost == 2:
            act.set_esc_us(steer_to_us(cfg, -0.2))
        if skorost == 3:
            act.set_esc_us(steer_to_us(cfg, -0.3))
        if skorost == 4:
            act.set_esc_us(steer_to_us(cfg, -0.4))
        if skorost == 5:
            act.set_esc_us(steer_to_us(cfg, -0.5))

            

    def clamp(x: float, lo: float, hi: float) -> float:
        return lo if x < lo else hi if x > hi else x

    def steer_to_us(cfg: Config, steer: float) -> int:
        steer = clamp(steer, -1.0, 1.0)
        if steer >= 0:
            return int(cfg.servo_center_us + steer * (cfg.servo_right_us - cfg.servo_center_us))
        return int(cfg.servo_center_us + steer * (cfg.servo_center_us - cfg.servo_left_us))

    cfg = Config()
    act = Actuators(cfg)

    act.stop()
    try:
        while True:
            time.sleep(1.0)

            act.set_esc_us(steer_to_us(cfg, -0.2))
            time.sleep(1.0)

            act.set_servo_us(steer_to_us(cfg, 0.3))
            time.sleep(1.0)
            act.set_servo_us(steer_to_us(cfg, 0.5))
            time.sleep(1.0)
            act.set_servo_us(steer_to_us(cfg, 0.0))
            time.sleep(1.0)

            act.set_esc_us(steer_to_us(cfg, -0.5))
            time.sleep(1.0)

            act.set_servo_us(steer_to_us(cfg, -0.1))
            time.sleep(1.0)
            act.set_servo_us(steer_to_us(cfg, -0.8))
            time.sleep(1.0)
            act.set_servo_us(steer_to_us(cfg, 0.0))
            time.sleep(1.0)

            act.set_esc_us(steer_to_us(cfg, 0.5))
            time.sleep(1.0)

            act.stop()
    except Exception as exc:
        print(exc)
    finally:
        act.stop()
