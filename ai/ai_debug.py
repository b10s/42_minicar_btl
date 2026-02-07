import json
import math
from pathlib import Path
import sys
import tkinter as tk

from ai.infer import AiModel
from tools.mock_lidar import load_frames
from utils import polar_to_xy


class Viewer(tk.Tk):
    def __init__(self, scans, pred_steer, log_steer, log_throttle):
        super().__init__()
        self.scans = scans
        self.pred_steer = pred_steer
        self.log_steer = log_steer
        self.log_throttle = log_throttle
        self.idx = 0
        self.scale = 80

        self.title("AI debug")
        self.canvas = tk.Canvas(self, width=900, height=600, bg="white")
        self.canvas.pack()

        bar = tk.Frame(self)
        bar.pack(fill=tk.X)
        self.label = tk.Label(bar, text="")
        self.label.pack(side=tk.LEFT, padx=8)
        tk.Button(bar, text="Prev", command=self.prev_frame).pack(side=tk.LEFT)
        tk.Button(bar, text="Next", command=self.next_frame).pack(side=tk.LEFT)

        self.bind("<Left>", lambda _e: self.prev_frame())
        self.bind("<Right>", lambda _e: self.next_frame())

        self.draw()

    def prev_frame(self):
        if not self.scans:
            return
        self.idx = (self.idx - 1) % len(self.scans)
        self.draw()

    def next_frame(self):
        if not self.scans:
            return
        self.idx = (self.idx + 1) % len(self.scans)
        self.draw()

    def _to_screen(self, x, y):
        cx = 450
        cy = 300
        return (cx + x * self.scale, cy - y * self.scale)

    def draw(self):
        self.canvas.delete("all")
        if not self.scans:
            return

        cx = 450
        cy = 300
        self.canvas.create_line(0, cy, 900, cy, fill="#ddd")
        self.canvas.create_line(cx, 0, cx, 600, fill="#ddd")

        scan = self.scans[self.idx]
        for a, d in scan:
            x, y = polar_to_xy(a, d)
            px, py = self._to_screen(x, y)
            self.canvas.create_oval(px - 2, py - 2, px + 2, py + 2, fill="#444", outline="")

        pred_deg = self.pred_steer[self.idx] / math.pi * 180.0
        log_deg = self.log_steer[self.idx] / math.pi * 180.0
        thr = self.log_throttle[self.idx]
        self.label.config(
            text=f"frame {self.idx+1}/{len(self.scans)} "
            f"pred={pred_deg:.2f}° log={log_deg:.2f}° thr={thr:.2f}"
        )


def _load_log(path: Path):
    scans = []
    log_steer = []
    log_throttle = []
    for row in load_frames(path):
        scans.append(row)
        log_steer.append(0.0)
        log_throttle.append(0.0)
    # If it is a drive_logger file, load_frames loses extra fields; re-read for steer/throttle.
    with path.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if i < len(log_steer):
                log_steer[i] = float(obj.get("steer", 0.0) or 0.0)
                log_throttle[i] = float(obj.get("throttle", 0.0) or 0.0)
    return scans, log_steer, log_throttle


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python ai_debug.py <file.jsonl> [model_dir]")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        return 2

    model_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("ai_out")
    model_path = model_dir / "model.onnx"
    stats_path = model_dir / "stats.json"
    if not model_path.exists() or not stats_path.exists():
        print("Missing model.onnx or stats.json")
        return 2

    model = AiModel(model_path, stats_path)
    scans, log_steer, log_throttle = _load_log(path)
    pred_steer = [model.predict_steer(scan) for scan in scans]

    Viewer(scans, pred_steer, log_steer, log_throttle).mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
