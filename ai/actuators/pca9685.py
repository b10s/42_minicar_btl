import board
import busio
from adafruit_pca9685 import PCA9685


def steer_to_us(steer: float, center_us: int, min_us: int, max_us: int) -> int:
    steer = min(max(-1.0, steer), 1.0)
    if steer >= 0.0:
        return int(center_us + steer * (max_us - center_us))
    return int(center_us + steer * (center_us - min_us))


def us_to_duty_cycle(us: int, freq_hz: int) -> int:
    period_us = 1_000_000.0 / freq_hz
    duty = int((us / period_us) * 65535)
    return min(max(0, duty), 65535)


class Actuators:
    def __init__(
        self,
        *,
        pca9685_address: int = 0x40,
        pca9685_freq_hz: int = 50,
        servo_channel: int = 0,
        esc_channel: int = 1,
        servo_center_us: int = 1500,
        esc_neutral_us: int = 1500,
    ):
        self.pca9685_address = pca9685_address
        self.pca9685_freq_hz = pca9685_freq_hz
        self.servo_channel = servo_channel
        self.esc_channel = esc_channel
        self.servo_center_us = servo_center_us
        self.esc_neutral_us = esc_neutral_us

        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c, address=self.pca9685_address)
        self.pca.frequency = self.pca9685_freq_hz

    def set_servo_us(self, us: int):
        duty = us_to_duty_cycle(us, self.pca9685_freq_hz)
        self.pca.channels[self.servo_channel].duty_cycle = duty

    def set_esc_us(self, us: int):
        duty = us_to_duty_cycle(us, self.pca9685_freq_hz)
        self.pca.channels[self.esc_channel].duty_cycle = duty

    def stop(self):
        self.set_esc_us(self.esc_neutral_us)
        self.set_servo_us(self.servo_center_us)


if __name__ == "__main__":
    import time

    # (center, min, max)
    SERVO_US = 1470, 1270, 1670
    ESC_US = 1500, 1000, 2000

    act = Actuators(
        servo_center_us=SERVO_US[0],
        esc_neutral_us=ESC_US[0],
    )
    act.stop()

    try:
        servo_vals = [-0.8, -0.8, 0.0, 0.2, 0.8]
        esc_vals = [-0.4, -0.4, 0.0, 0.0, 0.4]
        while True:
            for s, t in zip(servo_vals, esc_vals):
                s_us = steer_to_us(s, *SERVO_US)
                act.set_servo_us(s_us)
                t_us = steer_to_us(t, *ESC_US)
                act.set_esc_us(t_us)
                time.sleep(0.6)
            act.stop()
    except KeyboardInterrupt:
        pass
    finally:
        act.stop()
