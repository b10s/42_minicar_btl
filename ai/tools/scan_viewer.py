import json
import math
from pathlib import Path
import sys
import tkinter as tk

from config import Config


class ScanViewer:
    def __init__(self, path: Path):
        self.path = path
        self.cfg = Config()
        self.scans = self._load_scans(path)
        self.index = 0

        self.root = tk.Tk()
        self.root.title(f"Scan Viewer - {path.name}")

        self.canvas = tk.Canvas(self.root, width=800, height=800, bg="white")
        self.canvas.pack()

        ctrl = tk.Frame(self.root)
        ctrl.pack(fill=tk.X, padx=8, pady=6)

        self.prev_btn = tk.Button(ctrl, text="Prev", command=self.prev_scan)
        self.prev_btn.pack(side=tk.LEFT)
        self.next_btn = tk.Button(ctrl, text="Next", command=self.next_scan)
        self.next_btn.pack(side=tk.LEFT, padx=(6, 0))

        self.scale_var = tk.DoubleVar(value=120.0)
        tk.Label(ctrl, text="Scale px/m").pack(side=tk.LEFT, padx=(12, 4))
        self.scale_entry = tk.Entry(ctrl, textvariable=self.scale_var, width=6)
        self.scale_entry.pack(side=tk.LEFT)
        tk.Button(ctrl, text="Apply", command=self.render).pack(side=tk.LEFT, padx=(6, 0))

        self.show_sectors_var = tk.BooleanVar(value=True)
        self.show_filtered_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl, text="Sectors", variable=self.show_sectors_var, command=self.render).pack(
            side=tk.LEFT, padx=(12, 0)
        )
        tk.Checkbutton(ctrl, text="Show filtered", variable=self.show_filtered_var, command=self.render).pack(
            side=tk.LEFT, padx=(8, 0)
        )

        self.info = tk.Label(ctrl, text="")
        self.info.pack(side=tk.RIGHT)

        self.root.bind("<Left>", lambda _e: self.prev_scan())
        self.root.bind("<Right>", lambda _e: self.next_scan())
        self.root.bind("<space>", lambda _e: self.next_scan())

        self.render()
        self.root.mainloop()

    @staticmethod
    def _angle_in_sector(angle_deg: float, sector: tuple) -> bool:
        a = angle_deg % 360.0
        start, end = sector
        start = start % 360.0
        end = end % 360.0
        if start <= end:
            return start <= a <= end
        return a >= start or a <= end

    def _load_scans(self, path: Path):
        scans = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                scan = row.get("scan", [])
                scans.append((row.get("t", 0.0), scan))
        if not scans:
            raise RuntimeError("No scans found in file")
        return scans

    def render(self):
        t, scan = self.scans[self.index]
        self.canvas.delete("all")

        w = int(self.canvas["width"])
        h = int(self.canvas["height"])
        cx = w // 2
        cy = h // 2
        scale = float(self.scale_var.get() or 120.0)

        # axes
        self.canvas.create_line(0, cy, w, cy, fill="#ddd")
        self.canvas.create_line(cx, 0, cx, h, fill="#ddd")

        show_sectors = self.show_sectors_var.get()
        show_filtered = self.show_filtered_var.get()

        for ang, dist in scan:
            if dist <= 0:
                continue
            in_range = self.cfg.dist_min_m <= dist <= self.cfg.dist_max_m
            if not in_range and not show_filtered:
                continue
            a = math.radians(ang)
            x = dist * math.cos(a)
            y = dist * math.sin(a)
            px = cx + x * scale
            py = cy - y * scale
            if 0 <= px < w and 0 <= py < h:
                if not in_range:
                    color = "#bbb"
                elif show_sectors and self._angle_in_sector(ang, self.cfg.front_sector_deg):
                    color = "#43a047"
                elif show_sectors and self._angle_in_sector(ang, self.cfg.left_sector_deg):
                    color = "#e53935"
                elif show_sectors and self._angle_in_sector(ang, self.cfg.right_sector_deg):
                    color = "#1e88e5"
                else:
                    color = "black"
                self.canvas.create_oval(px - 2, py - 2, px + 2, py + 2, outline="", fill=color)

        self.info.config(text=f"{self.index+1}/{len(self.scans)}  t={t:.2f}")

    def prev_scan(self):
        self.index = (self.index - 1) % len(self.scans)
        self.render()

    def next_scan(self):
        self.index = (self.index + 1) % len(self.scans)
        self.render()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scan_viewer.py <file.jsonl>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2
    ScanViewer(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
