import math
import random
import statistics
from typing import List, Tuple, Optional
from config import Config

def angle_in_sector(deg: float, sector: tuple) -> bool:
    a, b = sector
    deg = deg % 360.0
    a = a % 360.0
    b = b % 360.0
    if a <= b:
        return a <= deg <= b
    return deg >= a or deg <= b

def polar_to_xy(angle_deg: float, dist_m: float) -> Tuple[float, float]:
    a = math.radians(angle_deg)
    x = dist_m * math.cos(a)
    y = dist_m * math.sin(a)
    return x, y

def downsample(points: List[Tuple[float, float]], n: int) -> List[Tuple[float, float]]:
    if n <= 0 or len(points) <= n:
        return points
    step = len(points) / n
    out = []
    i = 0.0
    while int(i) < len(points) and len(out) < n:
        out.append(points[int(i)])
        i += step
    return out

def line_from_2pts(p1: Tuple[float, float], p2: Tuple[float, float]) -> Optional[Tuple[float, float, float]]:
    x1, y1 = p1
    x2, y2 = p2
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) + abs(dy) < 1e-9:
        return None
    a = dy
    b = -dx
    norm = math.hypot(a, b)
    a /= norm
    b /= norm
    c = -(a * x1 + b * y1)
    return (a, b, c)

def point_line_dist(line: Tuple[float, float, float], p: Tuple[float, float]) -> float:
    a, b, c = line
    x, y = p
    return abs(a * x + b * y + c)

def refine_line_tls(points: List[Tuple[float, float]]) -> Optional[Tuple[float, float, float]]:
    if len(points) < 2:
        return None
    mx = sum(p[0] for p in points) / len(points)
    my = sum(p[1] for p in points) / len(points)
    sxx = sum((p[0] - mx) ** 2 for p in points)
    syy = sum((p[1] - my) ** 2 for p in points)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in points)

    if abs(sxy) < 1e-12 and abs(sxx - syy) < 1e-12:
        return None

    theta = 0.5 * math.atan2(2.0 * sxy, (sxx - syy))
    dx = math.cos(theta)
    dy = math.sin(theta)
    a = dy
    b = -dx
    norm = math.hypot(a, b)
    a /= norm
    b /= norm
    c = -(a * mx + b * my)
    return (a, b, c)

def ransac_wall_distance(
    points: List[Tuple[float, float]],
    iters: int = 80,
    inlier_thr: float = 0.05,
    min_inliers: int = 25,
) -> float:
    if len(points) < 2:
        return float("nan")

    best_line = None
    best_inliers: List[Tuple[float, float]] = []

    for _ in range(iters):
        p1, p2 = random.sample(points, 2)
        line = line_from_2pts(p1, p2)
        if line is None:
            continue
        inliers = [p for p in points if point_line_dist(line, p) <= inlier_thr]
        if len(inliers) > len(best_inliers):
            best_inliers = inliers
            best_line = line

    if best_line is None or len(best_inliers) < min_inliers:
        return float("nan")

    refined = refine_line_tls(best_inliers) or best_line
    a, b, c = refined
    return abs(c)

def compute_features(cfg: Config, scan_polar: List[Tuple[float, float]]) -> dict:
    left_pts = []
    right_pts = []
    front = []
    xy_all = []

    for ang, dist in scan_polar:
        if dist < cfg.dist_min_m or dist > cfg.dist_max_m:
            continue

        x, y = polar_to_xy(ang, dist)

        # basic ROI: ignore far-behind points (optional)
        if x < -0.3:
            continue

        if angle_in_sector(ang, cfg.left_sector_deg):
            left_pts.append((x, y))
        if angle_in_sector(ang, cfg.right_sector_deg):
            right_pts.append((x, y))
        if angle_in_sector(ang, cfg.front_sector_deg):
            front.append(dist)

        xy_all.append((x, y))

    d_left = ransac_wall_distance(left_pts)
    d_right = ransac_wall_distance(right_pts)
    min_front = min(front) if front else float("nan")
    curvature = statistics.pstdev(front) if len(front) >= 3 else float("nan")

    xy_all = downsample(xy_all, cfg.downsample_points)

    return {
        "d_left": d_left,
        "d_right": d_right,
        "min_front": min_front,
        "curvature": curvature,
        "scan_xy": xy_all,
    }
