import math
from config import Config

def compute_throttle(cfg: Config, steer: float, min_front: float, curvature: float) -> float:
    if not math.isnan(min_front) and min_front < cfg.emergency_front_m:
        return 0.0

    t = cfg.throttle_base
    t -= cfg.throttle_steer_penalty * abs(steer)

    if not math.isnan(curvature):
        if curvature < cfg.curvature_low:
            t = max(t, 0.35)
        elif curvature < cfg.curvature_mid:
            t = min(t, 0.30)
        else:
            t = min(t, 0.22)

    if t < cfg.throttle_min:
        t = cfg.throttle_min
    if t > cfg.throttle_max:
        t = cfg.throttle_max
    return t
