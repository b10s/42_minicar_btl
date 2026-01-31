import json
from dataclasses import dataclass, asdict
from pathlib import Path

RUNTIME_PATH = Path("runtime_config.json")

@dataclass
class RuntimeConfig:
    armed: bool = False
    kp: float = 0.9
    ki: float = 0.0
    kd: float = 0.18

def load_runtime(defaults: RuntimeConfig) -> RuntimeConfig:
    if not RUNTIME_PATH.exists():
        return defaults
    try:
        data = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
        return RuntimeConfig(
            armed=bool(data.get("armed", defaults.armed)),
            kp=float(data.get("kp", defaults.kp)),
            ki=float(data.get("ki", defaults.ki)),
            kd=float(data.get("kd", defaults.kd)),
        )
    except Exception:
        return defaults

def save_runtime(rc: RuntimeConfig) -> None:
    RUNTIME_PATH.write_text(json.dumps(asdict(rc), indent=2), encoding="utf-8")
