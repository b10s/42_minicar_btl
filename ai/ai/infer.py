import json
from pathlib import Path

import onnxruntime as ort

from features import scan_to_bins


class AiModel:
    def __init__(self, model_path: Path, stats_path: Path):
        self.session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
        self.roi_min_deg = stats["roi_min_deg"]
        self.roi_max_deg = stats["roi_max_deg"]
        self.bins = stats["bins"]
        self.dist_min_m = stats["dist_min_m"]
        self.dist_max_m = stats["dist_max_m"]
        self.x_mean = stats["x_mean"]
        self.x_std = stats["x_std"]

    def predict_steer(self, scan) -> float:
        x = scan_to_bins(
            scan,
            roi_min_deg=self.roi_min_deg,
            roi_max_deg=self.roi_max_deg,
            bins=self.bins,
            dist_min_m=self.dist_min_m,
            dist_max_m=self.dist_max_m,
        )
        x_norm = [(v - m) / s for v, m, s in zip(x, self.x_mean, self.x_std)]
        out = self.session.run(None, {"x": [x_norm]})
        return float(out[0][0][0])
