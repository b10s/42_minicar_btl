import json
import sys
import time

from config import Config
from sensors.ld06 import LD06


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "lidar_log.jsonl"

    cfg = Config()
    lidar = LD06(cfg.lidar_port, cfg.lidar_baud, offset_deg=cfg.angle_offset_deg)

    n = 0
    last_log = time.time()
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            while True:
                t0 = time.time()
                scan = lidar.read_scan()
                row = {
                    "t": t0,
                    "scan": scan,
                }
                f.write(json.dumps(row, separators=(",", ":")) + "\n")
                n += 1
                if t0 - last_log >= 2.0:
                    hz = n / (t0 - last_log)
                    print(f"hz={hz:.1f} scans={n} out={out_path}")
                    n = 0
                    last_log = t0
    except KeyboardInterrupt:
        pass
    finally:
        lidar.close()


if __name__ == "__main__":
    main()
