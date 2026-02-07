import asyncio
from dataclasses import dataclass, field
import threading
import time

from config import Config
from sensors.ld06 import LD06
from web.core import WebCore
from utils import polar_to_xy, downsample


@dataclass
class LocalState:
    lock: threading.Lock = field(default_factory=threading.Lock)

    scan_xy: list[tuple[float, float]] = field(default_factory=list)
    scan_ts: float = 0.0

    left_sector_deg: tuple[float, float] = (0.0, 0.0)
    right_sector_deg: tuple[float, float] = (0.0, 0.0)
    front_sector_deg: tuple[float, float] = (0.0, 0.0)

    sensor_hz: float = 0.0

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "t": time.time(),
                "scan_ts": self.scan_ts,
                "scan_xy": self.scan_xy,
                "sensor_hz": self.sensor_hz,
                "left_sector_deg": self.left_sector_deg,
                "right_sector_deg": self.right_sector_deg,
                "front_sector_deg": self.front_sector_deg,
            }


def compute_scan_xy(cfg: Config, scan: list[tuple[float, float]]) -> list[tuple[float, float]]:
    xy = []
    for ang, dist in scan:
        if dist < cfg.dist_min_m or dist > cfg.dist_max_m:
            continue
        x, y = polar_to_xy(ang, dist)
        xy.append((x, y))
    target_n = getattr(cfg, "downsample_points", None) or getattr(cfg, "feature_downsample_points", 0)
    return downsample(xy, int(target_n))


class MapServer(WebCore):
    def __init__(self, state: LocalState, telemetry_hz: float):
        super().__init__(state, telemetry_hz, on_ws_msg=None)


async def sensor_task(cfg: Config, st: LocalState, lidar: LD06):
    n = 0
    last_stat_t = time.time()
    while True:
        t0 = time.time()
        scan = lidar.read_scan()
        if scan:
            with st.lock:
                st.scan_xy = compute_scan_xy(cfg, scan)
                st.scan_ts = time.time()
            n += 1

        now = time.time()
        if now - last_stat_t >= 1.0:
            with st.lock:
                st.sensor_hz = n / (now - last_stat_t)
            n = 0
            last_stat_t = now

        dt = time.time() - t0
        sleep_t = max(0.0, (1.0 / cfg.sensor_hz) - dt) if cfg.sensor_hz > 0 else 0.0
        await asyncio.sleep(sleep_t)


async def main():
    cfg = Config()
    st = LocalState()

    with st.lock:
        st.left_sector_deg = cfg.left_sector_deg
        st.right_sector_deg = cfg.right_sector_deg
        st.front_sector_deg = cfg.front_sector_deg

    lidar = LD06(cfg.lidar_port, cfg.lidar_baud, offset_deg=cfg.angle_offset_deg)

    websrv = MapServer(st, cfg.telemetry_hz)
    runner = await websrv.run(host="0.0.0.0", port=8080)
    tasks = [
        asyncio.create_task(websrv.broadcaster()),
        asyncio.create_task(sensor_task(cfg, st, lidar)),
    ]

    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.cancel()
        lidar.close()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
