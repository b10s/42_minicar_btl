from pathlib import Path
from infer import AiModel

# Load the trained model
model = AiModel(
    model_path=Path("models/my_model/model.onnx"),
    stats_path=Path("models/my_model/stats.json")
)

# Load your test data
import json

rows = []
with open("test.jsonl", "r") as fh:
    for line in fh:
        if line.strip():
            rows.append(json.loads(line))

# Make predictions
for i, row in enumerate(rows):
    scan = row.get("scan") or []
    if scan:
        steer_prediction = model.predict_steer(scan)
        actual_steer = row.get("steer")
        print(f"Sample {i}: predicted={steer_prediction:.4f}, actual={actual_steer}")