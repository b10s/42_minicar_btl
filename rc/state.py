from dataclasses import dataclass, field
import math
import threading
import time
from typing import List, Tuple


def _sanitize(obj):
    # Convert NaN/Inf to None recursively, keep JSON-safe types
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


@dataclass
class SharedState:
    lock: threading.Lock = field(default_factory=threading.Lock)

    # Runtime params
    armed: bool = False
    kp: float = 0.9
    ki: float = 0.0
    kd: float = 0.18

    # Latest scan in XY (meters) in vehicle frame
    scan_xy: List[Tuple[float, float]] = field(default_factory=list)
    scan_ts: float = 0.0

    # Trail of scans for "map" view
    trail_xy: List[List[Tuple[float, float]]] = field(default_factory=list)

    # Derived distances/features
    d_left: float = float("nan")
    d_right: float = float("nan")
    min_front: float = float("nan")
    curvature: float = float("nan")

    # IMU
    yaw_rate: float = 0.0
    imu_ts: float = 0.0

    # Control outputs
    steer: float = 0.0
    throttle: float = 0.0
    steering_us: int = 1500
    esc_us: int = 1500

    # Diagnostics
    control_hz: float = 0.0
    sensor_hz: float = 0.0

    # Safety flags / errors (optional)
    last_error: str = ""

    def snapshot(self) -> dict:
        with self.lock:
            payload = {
                "t": time.time(),
                "armed": self.armed,
                "pid": {"kp": self.kp, "ki": self.ki, "kd": self.kd},

                "scan_ts": self.scan_ts,
                "imu_ts": self.imu_ts,

                "d_left": self.d_left,
                "d_right": self.d_right,
                "min_front": self.min_front,
                "curvature": self.curvature,

                "yaw_rate": self.yaw_rate,
                "steer": self.steer,
                "throttle": self.throttle,
                "steering_us": self.steering_us,
                "esc_us": self.esc_us,

                "control_hz": self.control_hz,
                "sensor_hz": self.sensor_hz,

                "scan_xy": self.scan_xy,
                "trail_xy": self.trail_xy,

                "last_error": self.last_error,
            }
        return _sanitize(payload)
