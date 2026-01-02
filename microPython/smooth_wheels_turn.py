from machine import Pin, PWM
import time

PULSE_NEUTRAL = 1480  # straight
PULSE_MIN     = 1240  # full left
PULSE_MAX     = 1720  # full right

PULSE_RANGE_LEFT  = PULSE_NEUTRAL - PULSE_MIN   # 240 us
PULSE_RANGE_RIGHT = PULSE_MAX - PULSE_NEUTRAL   # 240 us
FREQ = 50 

def clamp(x, lo, hi):
    if x < lo:
        return lo
    elif x > hi:
        return hi
    else:
        return x

def us_to_duty16(us, freq=FREQ):
    period_us = 1_000_000 // freq
    duty = int(us * 65535 // period_us)
    return clamp(duty, 0, 65535)

class ServoPWM:
    def __init__(self, pin_num, freq=FREQ):
        self.pwm = PWM(Pin(pin_num))
        self.pwm.freq(freq)
        self.freq = freq

    def write_us(self, us):
        self.pwm.duty_u16(us_to_duty16(us, self.freq))

    def deinit(self):
        self.pwm.deinit()

srv = ServoPWM(2)  # GP2
current_pos = 0.0

def servo_set_pos(pos):
    pos = clamp(pos, -100.0, 100.0)
    if pos < 0:
        rng = PULSE_RANGE_LEFT
    else:
        rng = PULSE_RANGE_RIGHT
    peak = pos * rng / 100.0
    srv.write_us(int(PULSE_NEUTRAL + peak))

def servo_turn_smooth(target_pos, time_ms=400, steps=40):
    global current_pos
    target_pos = clamp(target_pos, -100.0, 100.0)
    start = current_pos
    step_delay = max(1, time_ms // steps)

    for i in range(1, steps + 1):
        pos = start + (target_pos - start) * i / steps
        servo_set_pos(pos)
        time.sleep_ms(step_delay)

    current_pos = target_pos

# neutral position
servo_set_pos(0)
time.sleep_ms(500)

while True:
    servo_turn_smooth(-100, 1000, steps=60)
    time.sleep_ms(200)
    servo_turn_smooth(100,  1000, steps=60)
    time.sleep_ms(200)
    servo_turn_smooth(0,   500, steps=50)
    time.sleep_ms(200)