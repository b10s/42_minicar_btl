import math


def _norm_angle_deg(angle_deg: float) -> float:
    """Normalize to [-180, 180) degrees."""
    return ((angle_deg + 180.0) % 360.0) - 180.0


def scan_to_bins(
    scan,
    *,
    roi_min_deg: float = -90.0,
    roi_max_deg: float = 90.0,
    bins: int = 90,
    dist_min_m: float = 0.2,
    dist_max_m: float = 4.0,
):
    """Convert scan (angle_deg, dist_m) into min-distance bins over ROI."""
    if bins < 1:
        bins = 1
    span = max(1e-6, roi_max_deg - roi_min_deg)
    out = [dist_max_m] * bins
    for ang, dist in scan:
        if dist <= 0.0:
            continue
        if dist < dist_min_m or dist > dist_max_m:
            continue
        a = _norm_angle_deg(float(ang))
        if a < roi_min_deg or a > roi_max_deg:
            continue
        pos = (a - roi_min_deg) / span
        idx = int(pos * bins)
        if idx < 0:
            idx = 0
        elif idx >= bins:
            idx = bins - 1
        if dist < out[idx]:
            out[idx] = dist
    return out


def clamp(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def deg_to_rad(deg: float) -> float:
    return deg * math.pi / 180.0
