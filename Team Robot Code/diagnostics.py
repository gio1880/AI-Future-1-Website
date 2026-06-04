"""
diagnostics.py — Robot health check based on actual Pybricks source code.
               - robot health - 1. gyro drift, 2. motor sync, 3. turn accuracy, 4. battery voltage
SOURCE: github.com/pybricks/pybricks-micropython
        lib/pbio/src/imu.c           — gyro calibration & filter
        lib/pbio/src/control.c       — PID formula
        lib/pbio/include/pbio/control_settings.h — PID parameter names
        lib/pbio/src/drivebase.c     — DriveBase + gyro integration

KEY FACTS FROM SOURCE CODE:
─────────────────────────────────────────────────────────────────
  • hub.imu.ready() = "has been stationary at least once in last 10 min"
  • Gyro bias auto-calibrates via exponential moving average while still
  • reset_heading() only moves an offset — does NOT disturb the filter
  • angular_velocity() returns a Vector with .x .y .z in deg/s
  • DriveBase with use_gyro(True) uses 1D heading (direct axis integration)
    — NOT the quaternion. This is more accurate for flat-surface driving.
  • PID formula: torque = kp*pos_error + ki*integral + kd*speed_estimate
    The D term uses an ESTIMATED speed (smoother than raw derivative)
    - P - Proportional to current error
    - I - Integral of past error (helps with persistent bias, but can cause overshoot)
    - D - Derivative (based on estimated speed) helps prevent overshoot and oscillation
  • Adaptive kp: at low speed + small error, kp is reduced automatically
  • Model-based feedforward runs inside DriveBase — not user-tunable
  • hub.imu.settings() exposes: angular_velocity_bias, heading_correction,
    angular_velocity_scale, angular_velocity_threshold, acceleration_threshold
─────────────────────────────────────────────────────────────────

HOW TO RUN:
  Load onto hub, press center button. Results print via USB serial.
  Hub light: YELLOW=running, GREEN=pass, RED=fail.
"""

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.parameters import Port, Direction, Stop, Color, Axis
from pybricks.tools import wait

# ─────────────────────────────────────────────────────────────
# MATCH THESE TO YOUR ROBOT
# ─────────────────────────────────────────────────────────────
WHEEL_DIAMETER_MM = 56
AXLE_TRACK_MM     = 122
LEFT_PORT         = Port.A
RIGHT_PORT        = Port.E
LEFT_DIR          = Direction.COUNTERCLOCKWISE
RIGHT_DIR         = Direction.CLOCKWISE

# ─────────────────────────────────────────────────────────────
# PASS/FAIL THRESHOLDS
# ─────────────────────────────────────────────────────────────
GYRO_DRIFT_LIMIT_DEG_S  = 0.5   # max z-axis drift while at rest (deg/s)
MOTOR_SYNC_LIMIT_DEG    = 15    # max angle difference between motors after 2s
TURN_ACCURACY_LIMIT_DEG = 3     # max error after 4x 90° turns
BATTERY_MIN_MV          = 7400  # below ~80% charge, runs become inconsistent

# ─────────────────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────────────────
hub   = PrimeHub()
left  = Motor(LEFT_PORT, LEFT_DIR)
right = Motor(RIGHT_PORT, RIGHT_DIR)
robot = DriveBase(left, right, WHEEL_DIAMETER_MM, AXLE_TRACK_MM)
robot.use_gyro(True)

results = {}


# ─────────────────────────────────────────────────────────────
# TEST 1: GYRO DRIFT + BIAS READOUT
#
# Checks how much the z-axis (yaw) drifts at rest.
# Also prints the current auto-calibrated bias from hub.imu.settings()
# so you can see if it matches what's being measured live.
#
# From source: bias is auto-updated via exponential moving average
# every time the hub is stationary. After 3 detections it's saved to flash.
# angular_velocity() returns a Vector — access as .z (not [2])
# ─────────────────────────────────────────────────────────────
def test_gyro_drift():
    print("\n── TEST 1: Gyro Drift & Bias ──")
    print("Keep robot COMPLETELY STILL for 3 seconds...")
    hub.light.on(Color.YELLOW)

    timeout = 0
    while not hub.imu.ready():
        wait(100)
        timeout += 100
        if timeout > 5000:
            print("FAIL: hub.imu.ready() never returned True.")
            print("  Cause: hub was never stationary since boot.")
            print("  Fix: let hub sit still for 1-2 sec before running.")
            hub.light.on(Color.RED)
            results['gyro_drift'] = {'passed': False, 'reason': 'imu not ready'}
            return False

    # From official docs: hub.imu.angular_velocity(Axis.Z) returns a single
    # float (deg/s) — the yaw (heading) rotation rate. This is the cleanest way.
    # No indexing needed. Axis must be imported from pybricks.parameters.

    robot.reset()   # v3.6+: use robot.reset() not hub.imu.reset_heading()
    wait(300)

    max_drift = 0
    readings = []
    for _ in range(30):
        yaw = abs(hub.imu.angular_velocity(Axis.Z))   # single float, deg/s
        readings.append(yaw)
        if yaw > max_drift:
            max_drift = yaw
        wait(100)

    avg_drift = sum(readings) / len(readings)
    heading_after = hub.imu.heading()

    print("  Live z-axis drift: max={:.4f} deg/s  avg={:.4f} deg/s".format(
        max_drift, avg_drift))
    print("  Heading after 3s : {:.3f}°  (should be ~0)".format(heading_after))
    print("  Projected drift  : {:.2f} deg/min".format(avg_drift * 60))

    passed = max_drift < GYRO_DRIFT_LIMIT_DEG_S and abs(heading_after) < 1.0

    if passed:
        print("  PASS: Gyro is stable.")
        hub.light.on(Color.GREEN)
    else:
        print("  FAIL: Gyro drifting too much.")
        print("  TIP: Run calibrate_gyro_bias() from gyro_warmup.py to re-calibrate.")
        print("  TIP: Lower angular_velocity_threshold if hub isn't detecting stillness.")
        hub.light.on(Color.RED)

    results['gyro_drift'] = {
        'live_max_deg_s': round(max_drift, 4),
        'live_avg_deg_s': round(avg_drift, 4),
        'heading_drift_deg': round(heading_after, 3),
        'passed': passed
    }
    wait(800)
    return passed


# ─────────────────────────────────────────────────────────────
# TEST 2: MOTOR SYNCHRONIZATION
#
# Runs both motors open-loop at the same speed for 2 seconds.
# Compares encoder angles to see if they travel the same distance.
#
# From source (control.c): the PID D-term uses an estimated speed
# (observer/state estimator), not raw encoder differentiation.
# The adaptive kp reduces gain at low speeds/errors automatically.
# Model-based feedforward is baked in — you can't tune it directly.
#
# A large angle difference here means one motor is physically weaker
# (worn gear, loose cable, bad port). The heading_control PID can
# compensate, but only up to a point — if the gap is >50° it's a
# hardware problem, not a software one.
# ─────────────────────────────────────────────────────────────
def test_motor_sync():
    print("\n── TEST 2: Motor Synchronization ──")
    print("Robot will run both motors for 2s. Clear space ahead.")
    hub.light.on(Color.YELLOW)
    wait(2000)

    TEST_SPEED = 400  # deg/s — mid-range to avoid saturation

    left.reset_angle(0)
    right.reset_angle(0)

    left_log  = []
    right_log = []

    left.run(TEST_SPEED)
    right.run(TEST_SPEED)

    for _ in range(20):
        wait(100)
        left_log.append(left.angle())
        right_log.append(right.angle())

    left.brake()    # docs: Motor.stop() takes no args; use .brake() to hold
    right.brake()
    wait(400)

    final_left  = left_log[-1]
    final_right = right_log[-1]
    diff        = final_left - final_right
    abs_diff    = abs(diff)

    # Check early acceleration match (first 500ms = first 5 samples)
    early_diff = left_log[4] - right_log[4]

    print("\n  Time(ms)  Left°   Right°   Diff°")
    for i in range(len(left_log)):
        d = left_log[i] - right_log[i]
        print("  {:4d}      {:5d}   {:5d}    {:+d}".format(
            (i + 1) * 100, left_log[i], right_log[i], d))

    print("\n  Final angle difference : {}°  (limit: {})".format(abs_diff, MOTOR_SYNC_LIMIT_DEG))
    print("  Early acceleration gap : {:+d}°  (at 500ms)".format(early_diff))

    passed = abs_diff <= MOTOR_SYNC_LIMIT_DEG

    if passed:
        print("  PASS: Motors are well matched.")
        hub.light.on(Color.GREEN)
    else:
        direction = "LEFT faster — robot will drift RIGHT" if diff > 0 else "RIGHT faster — robot will drift LEFT"
        print("  FAIL: {} by {}°.".format(direction, abs_diff))
        print("  Software fix: increase heading_control kp to compensate.")
        print("  Hardware fix: check cable seating on the lagging motor port.")
        hub.light.on(Color.RED)

    results['motor_sync'] = {
        'left_deg': final_left,
        'right_deg': final_right,
        'diff_deg': diff,
        'early_accel_diff': early_diff,
        'passed': passed
    }
    wait(800)
    return passed


# ─────────────────────────────────────────────────────────────
# TEST 3: TURN ACCURACY — 4 × 90°
#
# The single best way to verify AXLE_TRACK_MM is correct.
# The 1D heading integration in the source uses:
#   single_axis_rotation += angular_velocity_calibrated.z * sample_time
# This is extremely accurate IF the gyro bias is well calibrated.
#
# A systematic turn error (e.g., always landing at 352° instead of 360°)
# means AXLE_TRACK_MM is wrong — not a PID problem.
# This test calculates the corrected value for you.
#
# Note: Pybricks heading is CUMULATIVE (does not wrap at 360).
# After 4x 90° turns, heading should read ~360°.
# ─────────────────────────────────────────────────────────────
def test_turn_accuracy():
    print("\n── TEST 3: Turn Accuracy (4 × 90°) ──")
    print("Robot turns right 4 times. Clear area around it.")
    hub.light.on(Color.YELLOW)
    wait(2000)

    # Slow, deliberate speed for accuracy measurement
    robot.settings(turn_rate=250, turn_acceleration=150)
    robot.reset()   # v3.6+: robot.reset() resets gyro heading + distance safely

    headings = []
    for i in range(4):
        robot.turn(90)
        wait(400)
        h = hub.imu.heading()
        headings.append(h)
        print("  Turn {}: heading={:.2f}°  (target {}°)".format(i + 1, h, (i + 1) * 90))

    final = hub.imu.heading()
    error = final - 360.0

    print("\n  Final heading : {:.2f}°  (expected 360°)".format(final))
    print("  Total error   : {:+.2f}°".format(error))

    if abs(error) > TURN_ACCURACY_LIMIT_DEG:
        # Corrected axle track calculation:
        # The turn distance = pi * axle_track * (angle/360)
        # If the robot turned more/less than expected, adjust proportionally
        suggested = round(AXLE_TRACK_MM * (360.0 / final), 2)
        print("\n  Your AXLE_TRACK_MM is probably {:.1f} mm  (you have {} mm)".format(
            suggested, AXLE_TRACK_MM))
        print("  Alternatively, run calibrate_heading_correction() from gyro_warmup.py")
        print("  to fix this at the gyro integration level instead.")

    passed = abs(error) <= TURN_ACCURACY_LIMIT_DEG

    if passed:
        print("  PASS: Turn accuracy good. AXLE_TRACK_MM is correct.")
        hub.light.on(Color.GREEN)
    else:
        print("  FAIL: Turns are {}.".format(
            "overshooting" if error > 0 else "undershooting"))
        hub.light.on(Color.RED)

    results['turn_accuracy'] = {
        'headings': [round(h, 2) for h in headings],
        'final': round(final, 2),
        'error': round(error, 2),
        'axle_track_used': AXLE_TRACK_MM,
        'passed': passed
    }
    wait(800)
    return passed


# ─────────────────────────────────────────────────────────────
# TEST 4: BATTERY VOLTAGE
#
# Motor output is voltage-limited. Low battery = less torque.
# The PID will try to compensate but it can only do so much.
# Below ~7400mV your straight runs and turns will be noticeably
# different from how the robot behaved at full charge.
# ─────────────────────────────────────────────────────────────
def test_battery():
    print("\n── TEST 4: Battery ──")
    v = hub.battery.voltage()
    a = hub.battery.current()
    pct = max(0, min(100, int((v - 6000) / (8400 - 6000) * 100)))

    print("  Voltage : {} mV  (~{}%)".format(v, pct))
    print("  Current : {} mA".format(a))

    passed = v >= BATTERY_MIN_MV
    if passed:
        print("  PASS: Battery OK.")
        hub.light.on(Color.GREEN)
    else:
        print("  FAIL: Charge the battery before competing!")
        hub.light.on(Color.RED)

    results['battery'] = {
        'voltage_mv': v, 'current_ma': a, 'est_pct': pct, 'passed': passed
    }
    wait(500)
    return passed


# ─────────────────────────────────────────────────────────────
# RUN ALL TESTS
# ─────────────────────────────────────────────────────────────
print("=" * 48)
print("  FLL DIAGNOSTIC SUITE  (Pybricks source-based)")
print("=" * 48)

r1 = test_gyro_drift()
r2 = test_motor_sync()
r3 = test_turn_accuracy()
r4 = test_battery()

print("\n" + "=" * 48)
print("  SUMMARY")
print("=" * 48)
all_ok = True
for name, result in results.items():
    status = "PASS" if result['passed'] else "FAIL ***"
    if not result['passed']:
        all_ok = False
    print("  {:25s}  {}".format(name, status))

print("-" * 48)
if all_ok:
    print("  ALL PASSED. Robot is ready to compete.")
    hub.light.on(Color.GREEN)
    hub.speaker.beep(frequency=800, duration=150)
    wait(80)
    hub.speaker.beep(frequency=1000, duration=150)
else:
    print("  ISSUES FOUND. Review output above.")
    hub.light.on(Color.RED)
    hub.speaker.beep(frequency=300, duration=600)
print("=" * 48)
