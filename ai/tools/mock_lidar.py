import json
from pathlib import Path
import time


def load_frames(path: Path):
    frames = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            scan = obj.get("scan") or []
            frames.append(scan)
    return frames


class MockLidar:
    def __init__(self, frames: list[list[tuple[float, float]]], *, loop: bool = True, rate_hz: float | None = None):
        self.frames = frames
        self.loop = loop
        self.rate_hz = rate_hz
        self.idx = 0
        self._last_t = time.time()

    def read_scan(self):
        if not self.frames:
            return []
        if self.rate_hz and self.rate_hz > 0:
            period = 1.0 / self.rate_hz
            now = time.time()
            dt = now - self._last_t
            if dt < period:
                time.sleep(period - dt)
            self._last_t = time.time()
        scan = self.frames[self.idx]
        self.idx += 1
        if self.idx >= len(self.frames):
            if self.loop:
                self.idx = 0
            else:
                self.idx = len(self.frames) - 1
        return scan


def load_mock_lidar(path: str | Path, *, loop: bool = True, rate_hz: float | None = None) -> MockLidar:
    frames = load_frames(Path(path))
    return MockLidar(frames, loop=loop, rate_hz=rate_hz)
