import board
import busio
from adafruit_pca9685 import PCA9685
from config import Config
import serial
import time
import math

# =========================
# LD06 CRC
# =========================

CRC8_TABLE = [
    0x00,0x4d,0x9a,0xd7,0x79,0x34,0xe3,0xae,0xf2,0xbf,0x68,0x25,0x8b,0xc6,0x11,0x5c,
    0xa9,0xe4,0x33,0x7e,0xd0,0x9d,0x4a,0x07,0x5b,0x16,0xc1,0x8c,0x22,0x6f,0xb8,0xf5,
    0x1f,0x52,0x85,0xc8,0x66,0x2b,0xfc,0xb1,0xed,0xa0,0x77,0x3a,0x94,0xd9,0x0e,0x43,
    0xb6,0xfb,0x2c,0x61,0xcf,0x82,0x55,0x18,0x44,0x09,0xde,0x93,0x3d,0x70,0xa7,0xea,
    0x3e,0x73,0xa4,0xe9,0x47,0x0a,0xdd,0x90,0xcc,0x81,0x56,0x1b,0xb5,0xf8,0x2f,0x62,
    0x97,0xda,0x0d,0x40,0xee,0xa3,0x74,0x39,0x65,0x28,0xff,0xb2,0x1c,0x51,0x86,0xcb,
    0x21,0x6c,0xbb,0xf6,0x58,0x15,0xc2,0x8f,0xd3,0x9e,0x49,0x04,0xaa,0xe7,0x30,0x7d,
    0x88,0xc5,0x12,0x5f,0xf1,0xbc,0x6b,0x26,0x7a,0x37,0xe0,0xad,0x03,0x4e,0x99,0xd4,
    0x7c,0x31,0xe6,0xab,0x05,0x48,0x9f,0xd2,0x8e,0xc3,0x14,0x59,0xf7,0xba,0x6d,0x20,
    0xd5,0x98,0x4f,0x02,0xac,0xe1,0x36,0x7b,0x27,0x6a,0xbd,0xf0,0x5e,0x13,0xc4,0x89,
    0x63,0x2e,0xf9,0xb4,0x1a,0x57,0x80,0xcd,0x91,0xdc,0x0b,0x46,0xe8,0xa5,0x72,0x3f,
    0xca,0x87,0x50,0x1d,0xb3,0xfe,0x29,0x64,0x38,0x75,0xa2,0xef,0x41,0x0c,0xdb,0x96,
    0x42,0x0f,0xd8,0x95,0x3b,0x76,0xa1,0xec,0xb0,0xfd,0x2a,0x67,0xc9,0x84,0x53,0x1e,
    0xeb,0xa6,0x71,0x3c,0x92,0xdf,0x08,0x45,0x19,0x54,0x83,0xce,0x60,0x2d,0xfa,0xb7,
    0x5d,0x10,0xc7,0x8a,0x24,0x69,0xbe,0xf3,0xaf,0xe2,0x35,0x78,0xd6,0x9b,0x4c,0x01,
    0xf4,0xb9,0x6e,0x23,0x8d,0xc0,0x17,0x5a,0x06,0x4b,0x9c,0xd1,0x7f,0x32,0xe5,0xa8
]

def crc8(data: bytes) -> int:
    c = 0
    for b in data:
        c = CRC8_TABLE[(c ^ b) & 0xFF]
    return c & 0xFF

# =========================
# LD06 Driver
# =========================

class LD06:
    FRAME_LEN = 47
    H0 = 0x54
    H1 = 0x2C

    def __init__(self, port, baud):
        self.ser = serial.Serial(port, baudrate=baud, timeout=0.4)
        self.offset_deg = 0.0

    def _read_frame(self):
        while True:
            b = self.ser.read(1)
            if not b:
                return None
            if b[0] != self.H0:
                continue
            b2 = self.ser.read(1)
            if not b2 or b2[0] != self.H1:
                continue
            rest = self.ser.read(self.FRAME_LEN - 2)
            if len(rest) != self.FRAME_LEN - 2:
                return None
            frame = bytes([self.H0, self.H1]) + rest
            if crc8(frame[:-1]) != frame[-1]:
                continue
            return frame

    def _parse_frame(self, frame):
        start_ang = int.from_bytes(frame[4:6], "little") / 100.0
        pts = []
        off = 6
        for _ in range(12):
            d = int.from_bytes(frame[off:off+2], "little")
            off += 3
            pts.append(d / 1000.0)
        end_ang = int.from_bytes(frame[off:off+2], "little") / 100.0

        diff = end_ang - start_ang
        if diff < -180: diff += 360
        if diff > 180: diff -= 360

        out = []
        for i, d in enumerate(pts):
            a = (start_ang + diff * i / 11.0 + self.offset_deg) % 360.0
            out.append((a, d))
        return out

    def read_scan(self, frames=60):
        scan = []
        for _ in range(frames):
            fr = self._read_frame()
            if not fr:
                break
            scan.extend(self._parse_frame(fr))
        scan.sort(key=lambda x: x[0])
        return scan

# =========================
# Actuators
# =========================

def us_to_duty(us, freq):
    return int(us * freq * 65535 / 1_000_000)

class Actuators:
    def __init__(self, cfg):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = PCA9685(i2c, address=cfg.pca9685_address)
        self.pca.frequency = cfg.pca9685_freq_hz
        self.cfg = cfg

    def set_servo_us(self, us):
        self.pca.channels[self.cfg.servo_channel].duty_cycle = us_to_duty(us, self.cfg.pca9685_freq_hz)

    def set_esc_us(self, us):
        self.pca.channels[self.cfg.esc_channel].duty_cycle = us_to_duty(us, self.cfg.pca9685_freq_hz)

    def stop(self):
        self.set_esc_us(self.cfg.esc_neutral_us)
        self.set_servo_us(self.cfg.servo_center_us)

# =========================
# Point Processing
# =========================

ANGLE_LIM = 70

def kdfilter_py(pts, radius=0.8, min_neighbors=5):
    r2 = radius * radius
    out = []
    for i, (xi, yi) in enumerate(pts):
        cnt = 0
        for j, (xj, yj) in enumerate(pts):
            if i == j:
                continue
            dx = xi - xj
            dy = yi - yj
            if dx*dx + dy*dy <= r2:
                cnt += 1
                if cnt >= min_neighbors:
                    out.append((xi, yi))
                    break
    return out

def scan_to_xy(scan):
    pts = []
    for ang, r in scan:
        if r is None or r < 0.4 or r > 7:
            continue
        if ang < ANGLE_LIM or ang > 360 - ANGLE_LIM:
            a = math.radians(ang)
            pts.append((r * math.cos(a), r * math.sin(a)))
    return kdfilter_py(pts)

def left_right_gap_decision_py(pts, radius=0.8, min_neighbors=3, eps=0.02):
    if not pts:
        return -1

    pts = sorted(pts, key=lambda p: p[0])
    r2 = radius * radius

    def valid(p):
        x, y = p
        cnt = 0
        for qx, qy in pts:
            dx = x - qx
            dy = y - qy
            if dx*dx + dy*dy <= r2:
                cnt += 1
                if cnt - 1 >= min_neighbors:
                    return True
        return False

    l, r = 0, len(pts) - 1
    while l < r and valid(pts[l]):
        l += 1
    while r > l and valid(pts[r]):
        r -= 1

    if l >= r:
        return 0

    gap = pts[r][0] - pts[l][0]
    if abs(gap) <= eps:
        return 0
    return 1 if gap > 0 else -1

# =========================
# Main Control Loop
# =========================

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def steer_to_us(cfg, s):
    s = clamp(s, -1, 1)
    if s >= 0:
        return int(cfg.servo_center_us + s * (cfg.servo_right_us - cfg.servo_center_us))
    return int(cfg.servo_center_us + s * (cfg.servo_center_us - cfg.servo_left_us))

if __name__ == "__main__":
    cfg = Config()
    act = Actuators(cfg)
    lidar = LD06("/dev/ttyS0", 230400)
    act.stop()

    try:
        while True:
            scan = lidar.read_scan()
            pts = scan_to_xy(scan)
            decision = left_right_gap_decision_py(pts)
            act.set_esc_us(steer_to_us(cfg, -0.075))

            if decision == 1:
                act.set_servo_us(steer_to_us(cfg, 0.8))
            elif decision == -1:
                act.set_servo_us(steer_to_us(cfg, -0.8))
            else:
                act.set_servo_us(steer_to_us(cfg, 0.0))

    except KeyboardInterrupt:
        pass
    finally:
        act.stop()
