"""
gyro_warmup.py — IMU initialization routines for FLL robot.

Based on official Pybricks v2.20.0 hub documentation:
  code.pybricks.com/static/docs/v2.20.0/hubs/primehub.html

KEY API FACTS FROM DOCS:
  hub.imu.ready()                    → True if calibrated within last 10 min
  hub.imu.stationary()               → True if still for at least 1 second
  hub.imu.angular_velocity(Axis.Z)   → single float, yaw rate in deg/s
  hub.imu.angular_velocity()         → vector along all axes (no indexing needed)
  hub.imu.reset_heading(angle)       → resets heading offset; raises OSError
                                        if DriveBase is actively using gyro
  hub.imu.settings(...)              → use keyword args to set; no-arg returns tuple
"""

from pybricks.parameters import Color, Axis
from pybricks.tools import wait


def warmup_imu(hub, max_wait_ms=5000):
    """
    Wait for the IMU to be ready and confirmed stationary, then zero heading.

    Call this ONCE at the start of menu.py — before any run is selected.
    Individual run files do NOT need to call this again.

    Uses hub.imu.stationary() (from docs: True if still for >= 1 second)
    instead of manually sampling angular_velocity — cleaner and more reliable.

    Returns True if ready, False if timed out.
    """

    hub.light.on(Color.YELLOW)

    # Step 1: Wait for hub.imu.ready()
    # Docs: "True when the robot has been sitting stationary for a few seconds,
    # which allows the device to re-calibrate. False if the hub has just been
    # started, or if it hasn't had a chance to calibrate for more than 10 min."
    elapsed = 0
    while not hub.imu.ready():
        wait(100)
        elapsed += 100
        if elapsed >= max_wait_ms:
            hub.light.on(Color.RED)
            print("WARNING: IMU not ready. Keep hub still before running.")
            return False

    # Step 2: Confirm hub is actually still right now using hub.imu.stationary()
    # Docs: "True if stationary for at least a second, False if it is moving."
    # Wait up to 3 more seconds for confirmed stillness.
    for _ in range(30):
        if hub.imu.stationary():
            break
        wait(100)

    # Step 3: Zero heading now that hub is confirmed still.
    # Docs: reset_heading() raises OSError if DriveBase is actively using gyro.
    # Safe here since no DriveBase moves have started yet.
    hub.imu.reset_heading(0)
    wait(50)

    hub.light.on(Color.GREEN)
    wait(150)
    hub.light.off()
    return True


def check_gyro_drift(hub, sample_ms=3000):
    """
    Measure yaw drift rate while hub is at rest. Useful for diagnostics.
    Keep robot COMPLETELY STILL during this call.

    From docs: hub.imu.angular_velocity(Axis.Z) returns a single float
    in deg/s — the yaw (heading rotation) rate.

    Returns average yaw drift in deg/s.
    """
    hub.imu.reset_heading(0)
    wait(200)

    samples = []
    n = sample_ms // 100
    for _ in range(n):
        # Axis.Z = yaw axis (heading rotation), single float returned
        yaw = abs(hub.imu.angular_velocity(Axis.Z))
        samples.append(yaw)
        wait(100)

    avg  = sum(samples) / len(samples)
    peak = max(samples)
    heading_drift = hub.imu.heading()

    print("Gyro drift over {}ms:".format(sample_ms))
    print("  avg  = {:.4f} deg/s  ({:.2f} deg/min)".format(avg, avg * 60))
    print("  peak = {:.4f} deg/s".format(peak))
    print("  heading accumulated = {:.3f} deg".format(heading_drift))
    return avg

