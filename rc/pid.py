import time

class PID:
    def __init__(self, kp: float, ki: float, kd: float, i_limit: float = 1.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.i_limit = abs(i_limit)
        self.i = 0.0
        self.prev_e = 0.0
        self.prev_t = None

    def reset(self):
        self.i = 0.0
        self.prev_e = 0.0
        self.prev_t = None

    def step(self, e: float, now: float | None = None) -> float:
        if now is None:
            now = time.time()
        if self.prev_t is None:
            self.prev_t = now
            self.prev_e = e
            return self.kp * e

        dt = now - self.prev_t
        if dt <= 1e-6:
            return self.kp * e

        de = (e - self.prev_e) / dt
        self.i += e * dt
        if self.i > self.i_limit:
            self.i = self.i_limit
        if self.i < -self.i_limit:
            self.i = -self.i_limit

        out = self.kp * e + self.ki * self.i + self.kd * de
        self.prev_t = now
        self.prev_e = e
        return out
