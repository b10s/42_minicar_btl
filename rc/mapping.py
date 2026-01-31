from collections import deque
from typing import List, Tuple

class TrailMap:
    def __init__(self, max_scans: int):
        self.buf = deque(maxlen=max_scans)

    def push(self, scan_xy: List[Tuple[float, float]]):
        self.buf.append(scan_xy)

    def get(self):
        return list(self.buf)
