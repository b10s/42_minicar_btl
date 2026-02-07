from dataclasses import dataclass


@dataclass
class Config:
    # ===== LiDAR =====
    lidar_port: str = "/dev/ttyS0"
    lidar_baud: int = 230400

    # ===== IMU =====
    imu_yaw_sign: int = -1
    imu_gyro_units: str = "auto"  # "rad/s" / "deg/s" / "auto"

    # ===== PCA9685 / I2C =====
    pca9685_address: int = 0x40
    pca9685_freq_hz: int = 50

    # PCA channels
    servo_channel: int = 0
    esc_channel: int = 1

    # ===== Servo calibration (microseconds) =====
    steer_sign: int = 1
    servo_center_us: int = 1470
    servo_left_us: int = 1230
    servo_right_us: int = 1700

    # ===== ESC calibration (microseconds) =====
    esc_forward_sign: int = -1
    esc_neutral_us: int = 1500
    esc_min_us: int = 1000
    esc_max_us: int = 2000

    # ===== Loops =====
    control_hz: float = 30.0
    telemetry_hz: float = 15.0

    # ===== Wall-follow sectors (degrees) =====
    # Assumption: LiDAR angles 0..360, with 0° pointing forward.
    angle_offset_deg: float = 0.0
    left_sector_deg: tuple = (50, 80)
    right_sector_deg: tuple = (280, 310)
    front_sector_deg: tuple = (330, 30)
    wall_min_points: int = 6
    wall_min_inlier_ratio: float = 0.45
    wall_ema_alpha: float = 0.35
    wall_desired_offset_m: float = 0.30
    wall_deadband_m: float = 0.03
    front_min_points: int = 4
    front_percentile: float = 5.0
    side_y_min_m: float = 0.25
    side_x_max_m: float = 0.60
    front_x_min_m: float = 0.25
    error_ema_alpha: float = 0.20
    max_steer_straight: float = 0.25

    # ===== Distance limits (meters) =====
    dist_min_m: float = 0.20
    dist_max_m: float = 4.00

    # ===== Emergency stop =====
    emergency_front_m: float = 0.25
    emergency_front_hyst_m: float = 0.05
    front_turn_on_m: float = 1.60
    front_turn_off_m: float = 1.90
    front_turn_steer: float = 0.95
    front_turn_hold_s: float = 0.40
    turn_hold_min_s: float = 0.30
    turn_exit_front_m: float = 1.80

    # ===== Steering PID defaults (can be overridden by runtime_config.json) =====
    kp: float = 0.5
    ki: float = 0.0
    kd: float = 0.18

    # yaw damping coefficient
    yaw_damp: float = 0.12

    # ===== Throttle settings =====
    throttle_base: float = 0.10
    throttle_min: float = 0.075
    throttle_max: float = 0.20
    throttle_steer_penalty: float = 0.12  # throttle -= penalty*abs(steer)
    throttle_invalid_wall: float = 0.075
    throttle_curve_exp: float = 1.5
    throttle_front_penalty: float = 0.08

    # Curvature thresholds (stddev of front distances)
    curvature_low: float = 0.08
    curvature_mid: float = 0.16

    # ===== Map/trail =====
    downsample_points: int = 180
    feature_downsample_points: int = 120

    steer_slew_rate: float = 3.5

    # ===== Safety / dropouts =====
    # If scan_ts is too old -> DISARM
    lidar_timeout_s: float = 0.6
    imu_timeout_s: float = 1.0
