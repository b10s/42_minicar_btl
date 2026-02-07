import sys

from evdev import InputDevice, ecodes, list_devices

from actuators.pca9685 import Actuators, steer_to_us
from config import Config
from utils import clamp

ABS_X = getattr(ecodes, "ABS_X", 0)
ABS_Z = getattr(ecodes, "ABS_Z", 2)
ABS_RZ = getattr(ecodes, "ABS_RZ", 5)


def _find_device(path: str | None):
    if path:
        return InputDevice(path)

    names = ("wireless controller", "dualsense", "sony")
    exclude = ("touchpad", "motion sensors")
    for dev_path in list_devices():
        dev = InputDevice(dev_path)
        name = (dev.name or "").lower()
        if any(x in name for x in names) and not any(x in name for x in exclude):
            return dev

    return None


def _norm_abs(dev: InputDevice, code: int, value: int) -> float:
    info = dev.absinfo(code)
    if not info:
        return 0.0
    span = max(1, info.max - info.min)
    return (value - info.min) / span


def main():
    dev_path = sys.argv[1] if len(sys.argv) > 1 else None
    dev = _find_device(dev_path)
    if dev is None:
        raise RuntimeError("DualSense not found. Provide /dev/input/eventX as arg.")
    print(f"Using input device: {dev.path} ({dev.name})")

    cfg = Config()
    act = Actuators(
        pca9685_address=cfg.pca9685_address,
        pca9685_freq_hz=cfg.pca9685_freq_hz,
        servo_channel=cfg.servo_channel,
        esc_channel=cfg.esc_channel,
        servo_center_us=cfg.servo_center_us,
        esc_neutral_us=cfg.esc_neutral_us,
    )
    act.stop()

    steer = 0.0
    throttle = 0.0
    r2 = 0.0
    l2 = 0.0
    deadzone = 0.05
    max_throttle = cfg.throttle_max

    try:
        for event in dev.read_loop():
            if event.type != ecodes.EV_ABS:
                continue
            if event.code == ABS_X:
                x = _norm_abs(dev, event.code, event.value) * 2.0 - 1.0
                steer = 0.0 if abs(x) < deadzone else x
            elif event.code == ABS_RZ or event.code == 5:
                r2 = _norm_abs(dev, event.code, event.value)
                throttle = clamp(r2 - l2, -max_throttle, max_throttle)
            elif event.code == ABS_Z or event.code == 2:
                l2 = _norm_abs(dev, event.code, event.value)
                throttle = clamp(r2 - l2, -max_throttle, max_throttle)
            else:
                continue

            steering_us = steer_to_us(
                cfg.steer_sign * steer,
                cfg.servo_center_us,
                cfg.servo_left_us,
                cfg.servo_right_us,
            )
            esc_us = steer_to_us(
                cfg.esc_forward_sign * throttle,
                cfg.esc_neutral_us,
                cfg.esc_min_us,
                cfg.esc_max_us,
            )
            act.set_servo_us(steering_us)
            act.set_esc_us(esc_us)
            print(
                f"steer={steer:.2f} throttle={throttle:.2f} "
                f"steer_us={steering_us} esc_us={esc_us}"
            )
    except KeyboardInterrupt:
        pass
    finally:
        act.stop()


if __name__ == "__main__":
    main()
