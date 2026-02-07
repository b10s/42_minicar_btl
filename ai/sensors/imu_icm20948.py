import time
import math

import board
import busio
from adafruit_icm20x import ICM20948


class IMU:
    def __init__(self, yaw_sign: int = 1, gyro_units: str = "auto"):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.imu = ICM20948(i2c, address=0x68)
        self.yaw_sign = -1 if yaw_sign < 0 else 1
        self.gyro_units = gyro_units

    def read(self) -> dict:
        gx, gy, gz = self.imu.gyro
        ax, ay, az = self.imu.acceleration
        mx, my, mz = self.imu.magnetic
        if self.gyro_units == "deg/s":
            yaw_rate = math.degrees(gz)
        else:
            # "rad/s" or "auto" -> assume rad/s from adafruit_icm20x
            yaw_rate = gz
        return {
            "t": time.time(),
            "yaw_rate": float(self.yaw_sign * yaw_rate),
            "accel_mag": float(math.sqrt(ax*ax + ay*ay + az*az)),
            "gyro_xyz": (float(gx), float(gy), float(gz)),
            "accel_xyz": (float(ax), float(ay), float(az)),
            "mag_xyz": (float(mx), float(my), float(mz)),
            "mag_mag": float(math.sqrt(mx*mx + my*my + mz*mz)),
        }


if __name__ == "__main__":
    imu = IMU()

    try:
        while True:
            data = imu.read()
            print(data)
    except KeyboardInterrupt:
        pass
