import time
import math

import board
import busio
from adafruit_icm20x import ICM20948


class IMU:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.imu = ICM20948(i2c, 0x68)

    def read(self) -> dict:
        gx, gy, gz = self.imu.gyro
        ax, ay, az = self.imu.acceleration
        return {
            "t": time.time(),
            "yaw_rate": float(gz),
            "accel_mag": float(math.sqrt(ax*ax + ay*ay + az*az)),
        }


if __name__ == "__main__":
    imu = IMU()

    try:
        while True:
            data = imu.read()
            print(data)
    except Exception as exc:
        print(exc)
