import argparse
import json
from pathlib import Path
import random

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from features import scan_to_bins


def _load_rows(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _build_dataset(rows, *, roi_min_deg, roi_max_deg, bins, dist_min_m, dist_max_m):
    xs = []
    ys = []
    for row in rows:
        scan = row.get("scan") or []
        if not scan:
            continue
        steer = row.get("steer")
        if steer is None:
            continue
        x = scan_to_bins(
            scan,
            roi_min_deg=roi_min_deg,
            roi_max_deg=roi_max_deg,
            bins=bins,
            dist_min_m=dist_min_m,
            dist_max_m=dist_max_m,
        )
        xs.append(x)
        ys.append([float(steer)])
    if not xs:
        raise RuntimeError("No valid samples in dataset.")
    x = np.asarray(xs, dtype=np.float32)
    y = np.asarray(ys, dtype=np.float32)
    return x, y


def _make_model(input_dim: int):
    return nn.Sequential(
        nn.Linear(input_dim, 64),
        nn.ReLU(),
        nn.Linear(64, 32),
        nn.ReLU(),
        nn.Linear(32, 1),
        nn.Tanh(),
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("data", type=Path, help="jsonl log file")
    ap.add_argument("--out", type=Path, default=Path("ai_out"), help="output dir")
    ap.add_argument("--roi-min", type=float, default=-90.0)
    ap.add_argument("--roi-max", type=float, default=90.0)
    ap.add_argument("--bins", type=int, default=90)
    ap.add_argument("--dist-min", type=float, default=0.2)
    ap.add_argument("--dist-max", type=float, default=4.0)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    rows = _load_rows(args.data)
    x, y = _build_dataset(
        rows,
        roi_min_deg=args.roi_min,
        roi_max_deg=args.roi_max,
        bins=args.bins,
        dist_min_m=args.dist_min,
        dist_max_m=args.dist_max,
    )

    idx = np.arange(len(x))
    np.random.shuffle(idx)
    split = int(0.9 * len(idx))
    tr_idx = idx[:split]
    va_idx = idx[split:]

    x_mean = x[tr_idx].mean(axis=0)
    x_std = x[tr_idx].std(axis=0) + 1e-6
    x_norm = (x - x_mean) / x_std

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    x_tr = torch.from_numpy(x_norm[tr_idx]).to(device)
    y_tr = torch.from_numpy(y[tr_idx]).to(device)
    x_va = torch.from_numpy(x_norm[va_idx]).to(device)
    y_va = torch.from_numpy(y[va_idx]).to(device)

    train_loader = DataLoader(TensorDataset(x_tr, y_tr), batch_size=args.batch, shuffle=True)

    model = _make_model(x.shape[1])
    model = model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.MSELoss()

    for epoch in range(1, args.epochs + 1):
        model.train()
        total = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            pred = model(xb)
            loss = loss_fn(pred, yb)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item() * xb.size(0)
        train_loss = total / max(1, len(x_tr))

        model.eval()
        with torch.no_grad():
            val_pred = model(x_va) if len(x_va) else None
            val_loss = loss_fn(val_pred, y_va).item() if val_pred is not None else 0.0
        print(f"epoch {epoch} train={train_loss:.4f} val={val_loss:.4f}")

    args.out.mkdir(parents=True, exist_ok=True)
    stats = {
        "roi_min_deg": args.roi_min,
        "roi_max_deg": args.roi_max,
        "bins": args.bins,
        "dist_min_m": args.dist_min,
        "dist_max_m": args.dist_max,
        "x_mean": x_mean.tolist(),
        "x_std": x_std.tolist(),
    }
    (args.out / "stats.json").write_text(json.dumps(stats), encoding="utf-8")

    onnx_path = args.out / "model.onnx"
    dummy = torch.zeros((1, x.shape[1]), dtype=torch.float32)
    torch.onnx.export(model, dummy, onnx_path, input_names=["x"], output_names=["y"], opset_version=14)
    print(f"saved {onnx_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
