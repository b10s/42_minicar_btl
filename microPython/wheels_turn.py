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

srv = ServoPWM(2)    # steering on GP2
motor = ServoPWM(4)  # ESC/motor on GP4

srv.write_us(PULSE_NEUTRAL)
motor.write_us(PULSE_NEUTRAL)

def servo_turn(pos, time_ms):
    pos = clamp(pos, -100.0, 100.0)
    rng = PULSE_RANGE_LEFT if pos < 0 else PULSE_RANGE_RIGHT
    peak = pos * rng / 100.0
    srv.write_us(int(PULSE_NEUTRAL + peak))
    time.sleep_ms(time_ms)

def motor_run(pos):
    pos = clamp(pos, -100.0, 100.0)
    rng = PULSE_RANGE_LEFT if pos < 0 else PULSE_RANGE_RIGHT
    peak = pos * rng / 100.0
    motor.write_us(int(PULSE_NEUTRAL + peak))

while True:
    motor_run(50)
    servo_turn(25, 1000)
    servo_turn(50, 1000)
    motor_run(100)
    servo_turn(75, 1000)
    servo_turn(50, 1000)
    servo_turn(25, 1000)
    motor_run(0)
    servo_turn(0, 2000)

    motor_run(-50)
    servo_turn(-25, 1000)
    servo_turn(-50, 1000)
    servo_turn(-75, 1000)
    motor_run(-100)
    servo_turn(-50, 1000)
    servo_turn(-25, 1000)
    motor_run(0)
    servo_turn(0, 2000)