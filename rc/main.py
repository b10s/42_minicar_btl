import asyncio
import time
import math
import logging

from log import setup_logging
setup_logging()

from config import Config
from state import SharedState
from runtime_config import RuntimeConfig, load_runtime

from sensors.ld06 import LD06
from sensors.imu_icm20948 import IMU
from actuators.pca9685 import Actuators

from control.pid import PID
from control.wall_follow import compute_features
from control.throttle import compute_throttle
from control.mapping import TrailMap

from web.server import WebServer

log_main = logging.getLogger("main")
log_sensors = logging.getLogger("sensors")
log_control = logging.getLogger("control")


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x

def steer_to_us(cfg: Config, steer: float) -> int:
    steer = clamp(steer, -1.0, 1.0)
    if steer >= 0:
        return int(cfg.servo_center_us + steer * (cfg.servo_right_us - cfg.servo_center_us))
    return int(cfg.servo_center_us + steer * (cfg.servo_center_us - cfg.servo_left_us))

def throttle_to_us(cfg: Config, throttle: float) -> int:
    throttle = clamp(throttle, 0.0, 1.0)
    return int(cfg.esc_neutral_us + throttle * (cfg.esc_max_us - cfg.esc_neutral_us))


async def sensor_task(cfg: Config, st: SharedState, lidar: LD06, imu: IMU | None, trail: TrailMap):
    last_stat_t = time.time()
    n = 0

    while True:
        # --- LiDAR MUST update scan_ts even if IMU fails ---
        try:
            scan = lidar.read_scan()
            feats = compute_features(cfg, scan)
            with st.lock:
                st.scan_xy = feats["scan_xy"]
                st.scan_ts = time.time()
                st.d_left = feats["d_left"]
                st.d_right = feats["d_right"]
                st.min_front = feats["min_front"]
                st.curvature = feats["curvature"]

                trail.push(st.scan_xy)
                st.trail_xy = trail.get()
        except Exception as e:
            with st.lock:
                st.last_error = f"lidar: {type(e).__name__}"
            log_sensors.exception("LiDAR read/parse failed")
            await asyncio.sleep(0.05)

        # --- IMU optional ---
        if imu is not None:
            try:
                imu_data = imu.read()
                with st.lock:
                    st.yaw_rate = imu_data["yaw_rate"]
                    st.imu_ts = imu_data["t"]
            except Exception:
                # Do not kill everything. Just mark IMU stale.
                with st.lock:
                    st.last_error = st.last_error or "imu: read failed"
                log_sensors.exception("IMU read failed")
                # fall back to yaw_rate=0 (control task will do that too)
                await asyncio.sleep(0)

        n += 1
        now = time.time()
        if now - last_stat_t >= 1.0:
            with st.lock:
                st.sensor_hz = n / (now - last_stat_t)
            n = 0
            last_stat_t = now

        await asyncio.sleep(0)


async def control_task(cfg: Config, st: SharedState, act: Actuators):
    with st.lock:
        kp, ki, kd = st.kp, st.ki, st.kd

    pid = PID(kp, ki, kd, i_limit=1.5)
    last_pid_key = f"{kp}|{ki}|{kd}"

    # hold-last-valid to avoid NaN blips stopping steering
    last_good_left = float("nan")
    last_good_right = float("nan")
    last_good_t = 0.0
    HOLD_S = 0.25

    period = 1.0 / cfg.control_hz
    last_stat_t = time.time()
    n = 0

    act.stop()
    log_control.info("Control loop started (%.1f Hz)", cfg.control_hz)

    while True:
        t0 = time.time()
        prev_armed = False
        armed_since = 0.0
        prev_throttle = 0.0
        kick_until = 0.0

        with st.lock:
            armed = st.armed
            d_left = st.d_left
            d_right = st.d_right
            min_front = st.min_front
            curvature = st.curvature
            yaw_rate = st.yaw_rate
            kp, ki, kd = st.kp, st.ki, st.kd
            scan_ts = st.scan_ts
            imu_ts = st.imu_ts

        now = time.time()
        if armed and not prev_armed:
            armed_since = now
        prev_armed = armed

        # --- Safety: we DISARM only on LiDAR timeout ---
        lidar_ok = (scan_ts != 0.0) and ((now - scan_ts) <= cfg.lidar_timeout_s)
        if armed and not lidar_ok:
            log_control.warning("Auto-DISARM: LiDAR timeout (age=%.3fs)", (now - scan_ts) if scan_ts else -1)
            with st.lock:
                st.armed = False
                st.last_error = "safety: lidar timeout"
            armed = False

        # --- IMU is optional: if stale -> yaw_rate=0 (no DISARM) ---
        imu_ok = (imu_ts != 0.0) and ((now - imu_ts) <= cfg.imu_timeout_s)
        if not imu_ok:
            yaw_rate = 0.0  # disable yaw damping if imu stale

        # --- PID hot reload ---
        pid_key = f"{kp}|{ki}|{kd}"
        if pid_key != last_pid_key:
            pid = PID(kp, ki, kd, i_limit=1.5)
            last_pid_key = pid_key
            log_control.info("PID updated to kp=%.3f ki=%.3f kd=%.3f", kp, ki, kd)

        if not armed:
            pid.reset()
            steer = 0.0
            throttle = 0.0
            steering_us = cfg.servo_center_us
            esc_us = cfg.esc_neutral_us
            act.set_servo_us(steering_us)
            act.set_esc_us(esc_us)
        else:
            # hold-last-valid to survive brief NaN
            if not math.isnan(d_left) and not math.isnan(d_right):
                last_good_left = d_left
                last_good_right = d_right
                last_good_t = now
            elif (now - last_good_t) <= HOLD_S:
                d_left = last_good_left
                d_right = last_good_right

            if math.isnan(d_left) or math.isnan(d_right):
                # degraded but not stop-steering violently
                steer = 0.0
                throttle = cfg.throttle_min
            else:
                error = d_left - d_right
                u = pid.step(error, now=t0)
                u -= cfg.yaw_damp * yaw_rate
                steer = clamp(u, -1.0, 1.0)
                throttle = compute_throttle(cfg, steer, min_front, curvature)

            steering_us = steer_to_us(cfg, steer)
            # kick when throttle rises from 0 -> >0
            if prev_throttle <= 0.01 and throttle > 0.01:
                kick_until = now + cfg.esc_kick_s
            prev_throttle = throttle

            if now < kick_until:
                esc_us = cfg.esc_kick_us
            else:
                esc_us = throttle_to_us(cfg, throttle)

            act.set_servo_us(steering_us)
            act.set_esc_us(esc_us)

        with st.lock:
            st.steer = steer
            st.throttle = throttle
            st.steering_us = steering_us
            st.esc_us = esc_us

        n += 1
        now2 = time.time()
        if now2 - last_stat_t >= 1.0:
            with st.lock:
                st.control_hz = n / (now2 - last_stat_t)
            n = 0
            last_stat_t = now2

        dt = time.time() - t0
        sleep_t = period - dt
        if sleep_t > 0:
            await asyncio.sleep(sleep_t)
        else:
            await asyncio.sleep(0)


async def main():
    cfg = Config()
    st = SharedState()
    trail = TrailMap(cfg.trail_scans)

    log_main.info("Starting rc_racer...")
    log_main.info("LiDAR: port=%s baud=%d", cfg.lidar_port, cfg.lidar_baud)

    defaults = RuntimeConfig(armed=False, kp=cfg.kp, ki=cfg.ki, kd=cfg.kd)
    rc = load_runtime(defaults)

    with st.lock:
        st.armed = False  # always start DISARMED
        st.kp = rc.kp
        st.ki = rc.ki
        st.kd = rc.kd

    lidar = LD06(cfg.lidar_port, cfg.lidar_baud)
    lidar.offset_deg = cfg.angle_offset_deg

    # IMU optional init (do not crash whole system)
    imu = None
    try:
        imu = IMU()
        log_main.info("IMU initialized")
    except Exception:
        log_main.exception("IMU init failed -> running without IMU (yaw damping disabled)")
        with st.lock:
            st.last_error = "imu: init failed"

    act = Actuators(cfg)
    log_main.info("Actuators initialized (PCA9685)")

    websrv = WebServer(st, cfg.telemetry_hz)
    runner = await websrv.run(host="0.0.0.0", port=8080)
    log_main.info("Web server started on :8080")

    tasks = [
        asyncio.create_task(websrv.broadcaster()),
        asyncio.create_task(sensor_task(cfg, st, lidar, imu, trail)),
        asyncio.create_task(control_task(cfg, st, act)),
    ]

    try:
        await asyncio.gather(*tasks)
    finally:
        for t in tasks:
            t.cancel()
        act.stop()
        lidar.close()
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
