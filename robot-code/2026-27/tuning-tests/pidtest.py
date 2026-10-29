# =========================
# IMPORTS
# =========================
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port
from pybricks.robotics import DriveBase
from pybricks.tools import wait

# =========================
# HUB & MOTORS
# =========================
hub = PrimeHub()

left_motor = Motor(Port.A)
right_motor = Motor(Port.E)

# =========================
# MOTOR ELECTRICAL SETTINGS
# =========================
left_motor.settings(max_voltage=8000)
right_motor.settings(max_voltage=8000)

# =========================
# MOTOR LIMITS (HIGH SPEED/ACCELERATION)
# =========================
left_motor.control.limits(speed=1200, acceleration=2000, torque=800)
right_motor.control.limits(speed=1200, acceleration=2000, torque=1000)

# =========================
# MOTOR PID (FAST + ACCURATE)
# =========================
left_motor.control.pid(kp=900, ki=0, kd=100, integral_deadzone=2, integral_rate=200)
right_motor.control.pid(kp=900, ki=0, kd=100, integral_deadzone=2, integral_rate=200)

# =========================
# MOTOR COMPLETION + STALL
# =========================
left_motor.control.target_tolerances(speed=20, position=1)
right_motor.control.target_tolerances(speed=20, position=1)

left_motor.control.stall_tolerances(speed=40, time=500)
right_motor.control.stall_tolerances(speed=40, time=500)

# =========================
# DRIVEBASE SETUP
# =========================
WHEEL_DIAMETER = 56   # mm
AXLE_TRACK = 122      # mm

drive = DriveBase(
    left_motor,
    right_motor,
    wheel_diameter=WHEEL_DIAMETER,
    axle_track=AXLE_TRACK
)

# =========================
# DRIVEBASE DEFAULT SPEEDS (FAST)
# =========================
drive.settings(
    straight_speed=400,        # mm/s
    straight_acceleration=1000,# mm/s²
    turn_rate=270,             # deg/s
    turn_acceleration=540      # deg/s²
)

# =========================
# ADVANCED DRIVEBASE PID (FAST + ACCURATE)
# =========================
# Distance control (straight)
drive.distance_control.pid(
    kp=15,
    ki=0,
    kd=80,
    integral_deadzone=2,
    integral_rate=50
)

# Heading control (turns & straight correction)
drive.heading_control.pid(
    kp=6,
    ki=0,
    kd=45,
    integral_deadzone=1,
    integral_rate=20
)

# =========================
# DEBUG / TUNING FUNCTIONS
# =========================

# ---- Motor PID test ----
def test_motor_pid(motor, target_deg):
    print("\n=== MOTOR PID TEST ===")
    motor.reset_angle(0)
    motor.run_target(500, target_deg)
    actual_angle = motor.angle()
    print("Motor:", motor, "Target:", target_deg, "Actual:", actual_angle, "Error:", actual_angle - target_deg)

# ---- Straight drive test ----
def test_straight(distance_mm):
    print("\n=== STRAIGHT TEST ===")
    print("Target distance:", distance_mm, "mm")
    drive.reset()
    hub.imu.reset_heading(0)
    start_heading = hub.imu.heading()
    drive.straight(distance_mm)
    actual_distance = drive.distance()
    end_heading = hub.imu.heading()
    print("Actual distance:", actual_distance, "mm")
    print("Distance error:", actual_distance - distance_mm, "mm")
    print("Heading drift:", end_heading - start_heading, "deg")

# ---- Turn test ----
def test_turn(angle_deg):
    print("\n=== TURN TEST ===")
    print("Target angle:", angle_deg, "deg")
    drive.reset()
    hub.imu.reset_heading(0)
    drive.turn(angle_deg)
    actual_heading = hub.imu.heading()
    print("Final heading:", actual_heading, "deg")
    print("Heading error:", actual_heading - angle_deg, "deg")

# ---- Turn oscillation check ----
def test_turn_oscillation(angle_deg):
    print("\n=== TURN OSCILLATION TEST ===")
    hub.imu.reset_heading(0)
    drive.turn(angle_deg)
    wait(200)
    h1 = hub.imu.heading()
    wait(200)
    h2 = hub.imu.heading()
    print("Heading after stop:", h1)
    print("Heading 200ms later:", h2)
    print("Post-stop drift:", h2 - h1)

# ---- Motor balance check ----
def motor_balance_check():
    print("\n=== MOTOR BALANCE TEST ===")
    left_motor.reset_angle(0)
    right_motor.reset_angle(0)
    drive.straight(300)
    left_angle = left_motor.angle()
    right_angle = right_motor.angle()
    print("Left motor angle:", left_angle)
    print("Right motor angle:", right_angle)
    print("Difference:", left_angle - right_angle)

# =========================
# MAIN TEST SEQUENCE
# =========================
print("\n===== PID DEBUG SESSION START =====")

# Test motor PID individually
# test_motor_pid(left_motor, 720)
# test_motor_pid(right_motor, 720)
# wait(500)

# # Test straight drive
test_straight(300)
wait(500)

# # Test turns
# test_turn(90)
# wait(500)
# test_turn(-90)
# wait(500)

# # Oscillation check
# test_turn_oscillation(90)
# wait(500)

# # Motor balance
# motor_balance_check()

print("\n===== PID DEBUG SESSION END =====")
