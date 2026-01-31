from dataclasses import dataclass

@dataclass
class Config:
    # ===== LiDAR =====
    lidar_port: str = "/dev/ttyS0"
    lidar_baud: int = 230400

    # ===== IMU (MPU-6050) =====
    imu_yaw_sign: int = 1          # или -1
    imu_gyro_units: str = "auto"   # "rad/s" / "deg/s" / "auto"

    # ===== PCA9685 / I2C =====
    pca9685_address: int = 0x40
    pca9685_freq_hz: int = 50

    # PCA channels
    servo_channel: int = 0
    esc_channel: int = 1

    # ===== Servo calibration (microseconds) =====
    servo_center_us: int = 1500
    servo_left_us: int = 1000
    servo_right_us: int = 2000

    # ===== ESC calibration (microseconds) =====
    esc_neutral_us: int = 1500
    esc_min_us: int = 1000
    esc_max_us: int = 2000
    esc_deadband_us: int = 80
    esc_min_forward_us: int = 1650
    esc_kick_us: int = 1800
    esc_kick_s: float = 0.12

    # ===== Loops =====
    control_hz: float = 30.0
    telemetry_hz: float = 15.0

    # ===== Wall-follow sectors (degrees) =====
    # Assumption: LiDAR angles 0..360, with 0° pointing forward.
    angle_offset_deg: float = 90.0
    left_sector_deg: tuple = (60, 120)
    right_sector_deg: tuple = (240, 300)
    front_sector_deg: tuple = (350, 10)

    # ===== Distance limits (meters) =====
    dist_min_m: float = 0.10
    dist_max_m: float = 4.00

    # ===== Emergency stop =====
    emergency_front_m: float = 0.35

    # ===== Steering PID defaults (can be overridden by runtime_config.json) =====
    kp: float = 0.9
    ki: float = 0.0
    kd: float = 0.18

    # yaw damping coefficient
    yaw_damp: float = 0.12

    # ===== Throttle settings =====
    throttle_base: float = 0.17
    throttle_min: float = 0.17
    throttle_max: float = 0.45
    throttle_steer_penalty: float = 0.25  # throttle -= penalty*abs(steer)

    # Curvature thresholds (stddev of front distances)
    curvature_low: float = 0.08
    curvature_mid: float = 0.16

    # ===== Map/trail =====
    trail_scans: int = 25
    downsample_points: int = 180

    # ===== Safety / dropouts =====
    # If scan_ts is too old -> DISARM
    lidar_timeout_s: float = 0.6
    imu_timeout_s: float = 1.0
