import logging
import math
import os
import sys


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def rad_to_deg(rad: float) -> float:
    return math.degrees(rad)


def deg_to_rad(deg: float) -> float:
    return math.radians(deg)


def angle_in_sector(deg: float, sector: tuple[float, float]) -> bool:
    a, b = sector
    deg = deg % 360.0
    a = a % 360.0
    b = b % 360.0
    if a <= b:
        return a <= deg <= b
    return deg >= a or deg <= b


def polar_to_xy(angle_deg: float, dist_m: float) -> tuple[float, float]:
    a = deg_to_rad(angle_deg)
    x = dist_m * math.cos(a)
    y = dist_m * math.sin(a)
    return x, y


def downsample(points: list[tuple[float, float]], target_n: int) -> list[tuple[float, float]]:
    if target_n <= 0 or len(points) <= target_n:
        return points
    step = len(points) / target_n
    out = []
    i = 0.0
    while int(i) < len(points) and len(out) < target_n:
        out.append(points[int(i)])
        i += step
    return out


def line_from_2pts(p1: tuple[float, float], p2: tuple[float, float]) -> tuple[float, float, float] | None:
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


def point_line_dist(line: tuple[float, float, float], p: tuple[float, float]) -> float:
    a, b, c = line
    x, y = p
    return abs(a * x + b * y + c)


def refine_line_tls(points: list[tuple[float, float]]) -> tuple[float, float, float] | None:
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


def circle_from_3pts(
    p1: tuple[float, float], p2: tuple[float, float], p3: tuple[float, float]
) -> tuple[float, float, float] | None:
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    d = 2.0 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return None
    x1sq = x1 * x1 + y1 * y1
    x2sq = x2 * x2 + y2 * y2
    x3sq = x3 * x3 + y3 * y3
    ux = (x1sq * (y2 - y3) + x2sq * (y3 - y1) + x3sq * (y1 - y2)) / d
    uy = (x1sq * (x3 - x2) + x2sq * (x1 - x3) + x3sq * (x2 - x1)) / d
    r = math.hypot(ux - x1, uy - y1)
    return ux, uy, r


def side_point_ok(x: float, y: float, side: str, side_x_max_m: float, side_y_min_m: float) -> bool:
    if x > side_x_max_m:
        return False
    if side == "left":
        return y >= side_y_min_m
    if side == "right":
        return y <= -side_y_min_m
    return True


def setup_logging():
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
