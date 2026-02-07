from dataclasses import dataclass
import random
import statistics

from config import Config
from utils import (
    angle_in_sector,
    polar_to_xy,
    side_point_ok,
    downsample,
    line_from_2pts,
    point_line_dist,
    refine_line_tls,
)


@dataclass
class Features:
    d_left: float
    d_right: float
    min_front: float
    curvature: float
    scan_xy: list[tuple[float, float]]
    left_xy: list[tuple[float, float]]
    right_xy: list[tuple[float, float]]
    front_xy: list[tuple[float, float]]
    left_points: int
    right_points: int
    left_inliers: int
    right_inliers: int


def ransac_wall_distance(
    points: list[tuple[float, float]],
    iters: int = 40,
    inlier_thr: float = 0.05,
) -> tuple[float, int]:
    if len(points) < 2:
        return float("nan"), 0

    best_line = None
    best_inliers: list[tuple[float, float]] = []

    for _ in range(iters):
        p1, p2 = random.sample(points, 2)
        line = line_from_2pts(p1, p2)
        if line is None:
            continue
        inliers = [p for p in points if point_line_dist(line, p) <= inlier_thr]
        if len(inliers) > len(best_inliers):
            best_inliers = inliers
            best_line = line

    if best_line is None:
        return float("nan"), 0

    refined = refine_line_tls(best_inliers) or best_line
    a, b, c = refined
    return abs(c), len(best_inliers)


def _partition_scan(cfg: Config, scan_polar: list[tuple[float, float]]):
    left_pts: list[tuple[float, float]] = []
    right_pts: list[tuple[float, float]] = []
    front: list[float] = []
    left_xy: list[tuple[float, float]] = []
    right_xy: list[tuple[float, float]] = []
    front_xy: list[tuple[float, float]] = []
    xy_all: list[tuple[float, float]] = []

    for ang, dist in scan_polar:
        if dist < cfg.dist_min_m or dist > cfg.dist_max_m:
            continue

        x, y = polar_to_xy(ang, dist)

        if x < -0.3:
            continue

        if angle_in_sector(ang, cfg.left_sector_deg):
            if side_point_ok(x, y, "left", cfg.side_x_max_m, cfg.side_y_min_m):
                left_pts.append((x, y))
                left_xy.append((x, y))
        if angle_in_sector(ang, cfg.right_sector_deg):
            if side_point_ok(x, y, "right", cfg.side_x_max_m, cfg.side_y_min_m):
                right_pts.append((x, y))
                right_xy.append((x, y))
        if angle_in_sector(ang, cfg.front_sector_deg):
            if x >= cfg.front_x_min_m:
                front.append(dist)
                front_xy.append((x, y))

        xy_all.append((x, y))

    return left_pts, right_pts, front, left_xy, right_xy, front_xy, xy_all


def _estimate_walls(cfg: Config, left_pts, right_pts):
    left_inliers = 0
    right_inliers = 0

    if len(left_pts) >= cfg.wall_min_points:
        d_left, left_inliers = ransac_wall_distance(left_pts)
    else:
        d_left = float("nan")
    if len(right_pts) >= cfg.wall_min_points:
        d_right, right_inliers = ransac_wall_distance(right_pts)
    else:
        d_right = float("nan")

    if len(left_pts) > 0 and left_inliers / len(left_pts) < cfg.wall_min_inlier_ratio:
        d_left = float("nan")
    if len(right_pts) > 0 and right_inliers / len(right_pts) < cfg.wall_min_inlier_ratio:
        d_right = float("nan")

    return d_left, d_right, left_inliers, right_inliers


def _front_stats(cfg: Config, front: list[float]):
    min_front = float("nan")
    if len(front) >= cfg.front_min_points:
        front_sorted = sorted(front)
        idx = int((cfg.front_percentile / 100.0) * (len(front_sorted) - 1))
        idx = max(0, min(idx, len(front_sorted) - 1))
        min_front = front_sorted[idx]
    curvature = statistics.pstdev(front) if len(front) >= 3 else float("nan")
    return min_front, curvature


def compute_features(cfg: Config, scan_polar: list[tuple[float, float]]) -> Features:
    left_pts, right_pts, front, left_xy, right_xy, front_xy, xy_all = _partition_scan(cfg, scan_polar)
    d_left, d_right, left_inliers, right_inliers = _estimate_walls(cfg, left_pts, right_pts)
    min_front, curvature = _front_stats(cfg, front)

    xy_all = downsample(xy_all, cfg.downsample_points)
    debug_n = min(cfg.downsample_points, 120)
    left_xy = downsample(left_xy, debug_n)
    right_xy = downsample(right_xy, debug_n)
    front_xy = downsample(front_xy, debug_n)

    return Features(
        d_left=d_left,
        d_right=d_right,
        min_front=min_front,
        curvature=curvature,
        scan_xy=xy_all,
        left_xy=left_xy,
        right_xy=right_xy,
        front_xy=front_xy,
        left_points=len(left_pts),
        right_points=len(right_pts),
        left_inliers=left_inliers,
        right_inliers=right_inliers,
    )
