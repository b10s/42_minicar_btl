import argparse
import sys

from actuators.pca9685 import Actuators, steer_to_us
from config import Config
from sensors.imu_icm20948 import IMU


def _prompt_loop(title: str, get_us, set_us, step: int = 5):
    print(title)
    print("Commands: '+', '-', 'set <us>', 'step <us>', 'show', 'quit'")
    while True:
        cmd = input("> ").strip()
        if cmd == "+":
            set_us(get_us() + step)
        elif cmd == "-":
            set_us(get_us() - step)
        elif cmd.startswith("set "):
            try:
                val = int(cmd.split()[1])
                set_us(val)
            except Exception:
                print("Bad value")
        elif cmd.startswith("step "):
            try:
                step = int(cmd.split()[1])
                print(f"Step = {step} us")
            except Exception:
                print("Bad value")
        elif cmd == "show":
            print(f"Current: {get_us()} us")
        elif cmd in ("q", "quit", "exit"):
            break
        else:
            print("Unknown command")


def _make_act(cfg: Config) -> Actuators:
    return Actuators(
        pca9685_address=cfg.pca9685_address,
        pca9685_freq_hz=cfg.pca9685_freq_hz,
        servo_channel=cfg.servo_channel,
        esc_channel=cfg.esc_channel,
        servo_center_us=cfg.servo_center_us,
        esc_neutral_us=cfg.esc_neutral_us,
    )


def _adjust_value(title: str, initial: int, apply_fn, step: int = 5) -> int:
    current = initial

    def get_us():
        return current

    def set_us(us):
        nonlocal current
        current = int(us)
        apply_fn(current)
        print(f"value = {current}")

    _prompt_loop(title, get_us, set_us, step=step)
    return current


def calibrate_servo_center(act: Actuators, cfg: Config):
    current = cfg.servo_center_us

    def apply_center(us: int):
        act.set_servo_us(us)
        print(f"servo_center_us = {us}")

    act.set_esc_us(cfg.esc_neutral_us)
    apply_center(current)
    _adjust_value("Servo center calibration", current, apply_center)


def calibrate_servo_range(act: Actuators, cfg: Config):
    left = cfg.servo_left_us
    right = cfg.servo_right_us

    def apply_left(us: int):
        nonlocal left
        left = us
        act.set_servo_us(us)
        print(f"servo_left_us = {us}")

    def apply_right(us: int):
        nonlocal right
        right = us
        act.set_servo_us(us)
        print(f"servo_right_us = {us}")

    act.set_esc_us(cfg.esc_neutral_us)
    print("Adjust LEFT limit first (steer full left).")
    _adjust_value("Servo LEFT limit", left, apply_left)
    print("Adjust RIGHT limit next (steer full right).")
    _adjust_value("Servo RIGHT limit", right, apply_right)


def calibrate_esc_neutral(act: Actuators, cfg: Config):
    current = cfg.esc_neutral_us

    def apply_neutral(us: int):
        act.set_esc_us(us)
        print(f"esc_neutral_us = {us}")

    act.set_servo_us(cfg.servo_center_us)
    apply_neutral(current)
    _adjust_value("ESC neutral calibration", current, apply_neutral, step=2)


def calibrate_esc_range(act: Actuators, cfg: Config):
    min_us = cfg.esc_min_us
    max_us = cfg.esc_max_us

    def apply_min(us: int):
        nonlocal min_us
        min_us = us
        act.set_esc_us(us)
        print(f"esc_min_us = {us}")

    def apply_max(us: int):
        nonlocal max_us
        max_us = us
        act.set_esc_us(us)
        print(f"esc_max_us = {us}")

    act.set_servo_us(cfg.servo_center_us)
    print("Adjust ESC MIN (reverse) carefully.")
    _adjust_value("ESC MIN", min_us, apply_min, step=5)
    print("Adjust ESC MAX (forward) carefully.")
    _adjust_value("ESC MAX", max_us, apply_max, step=5)


def calibrate_steer_sign(act: Actuators, cfg: Config):
    act.set_esc_us(cfg.esc_neutral_us)
    print("Setting steer = +0.4. If wheels turn LEFT, steer_sign should be 1.")
    print("If wheels turn RIGHT, steer_sign should be -1.")
    us = steer_to_us(0.4, cfg.servo_center_us, cfg.servo_left_us, cfg.servo_right_us)
    act.set_servo_us(us)
    input("Press Enter to center...")
    act.set_servo_us(cfg.servo_center_us)


def calibrate_imu_sign(cfg: Config):
    try:
        imu = IMU(yaw_sign=1, gyro_units=cfg.imu_gyro_units)
    except Exception as exc:
        print(f"IMU init failed: {exc}")
        return

    print("Rotate the car LEFT (CCW) by hand, then press Enter to sample yaw_rate.")
    input("Ready? ")
    data = imu.read()
    yaw = data.get("yaw_rate", 0.0)
    print(f"yaw_rate = {yaw:.3f}")
    if yaw >= 0:
        print("Suggest: imu_yaw_sign = 1")
    else:
        print("Suggest: imu_yaw_sign = -1")


def main():
    parser = argparse.ArgumentParser(description="RC racer calibration helper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("servo-center", help="Calibrate servo center (servo_center_us)")
    sub.add_parser("servo-range", help="Calibrate servo left/right limits")
    sub.add_parser("esc-neutral", help="Calibrate ESC neutral (esc_neutral_us)")
    sub.add_parser("esc-range", help="Calibrate ESC min/max")
    sub.add_parser("steer-sign", help="Check steering sign (steer_sign)")
    sub.add_parser("imu-sign", help="Check IMU yaw sign (imu_yaw_sign)")

    args = parser.parse_args()
    cfg = Config()
    act = _make_act(cfg)

    try:
        if args.cmd == "servo-center":
            calibrate_servo_center(act, cfg)
        elif args.cmd == "servo-range":
            calibrate_servo_range(act, cfg)
        elif args.cmd == "esc-neutral":
            calibrate_esc_neutral(act, cfg)
        elif args.cmd == "esc-range":
            calibrate_esc_range(act, cfg)
        elif args.cmd == "steer-sign":
            calibrate_steer_sign(act, cfg)
        elif args.cmd == "imu-sign":
            calibrate_imu_sign(cfg)
        else:
            print("Unknown command")
            return 2
    finally:
        act.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
