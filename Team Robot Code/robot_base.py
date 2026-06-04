"""
robot_base.py — Single source of truth for robot hardware setup.
Based on official Pybricks v3.6+ documentation.

HOW TO USE IN A RUN FILE:
    from robot_base import hub, RAM, LAM, make_robot

    robot = make_robot()                  # default 122 mm axle track
    robot = make_robot(axle_track=101.6)  # Run_A override
    robot = make_robot(axle_track=152)    # Run_D override

    robot.settings(straight_speed=600, straight_acceleration=300, ...)
    # ... your mission code ...

WHY make_robot() instead of importing robot directly:
    Pybricks v3.6 made hub.imu.reset_heading() raise OSError (EBUSY) if
    any DriveBase has use_gyro(True) active. The safe replacement is
    robot.reset(), which is called automatically inside make_robot().
    Never call hub.imu.reset_heading() in your run files.
"""

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.parameters import Port, Direction, Stop
from pybricks.tools import wait

# ─────────────────────────────────────────────
# ROBOT PHYSICAL CONSTANTS
#
# HOW TO CALIBRATE (from official docs):
#   wheel_diameter: Run straight(1000) and measure actual distance.
#     - Traveled too short → decrease WHEEL_DIAMETER_MM
#     - Traveled too far   → increase WHEEL_DIAMETER_MM
#
#   axle_track: FIRST fix wheel_diameter above. Then run turn(360).
#     - Turned too little  → increase AXLE_TRACK_MM
#     - Turned too far     → decrease AXLE_TRACK_MM
# ─────────────────────────────────────────────
WHEEL_DIAMETER_MM = 56      # mm
AXLE_TRACK_MM     = 122     # mm — default; override per-run via make_robot()

# ─────────────────────────────────────────────
# HARDWARE INIT — one hub, one set of motors, shared across all run files.
# Importing this module from Menu.py or a run file will initialize these
# exactly once (Python caches modules after the first import).
# ─────────────────────────────────────────────
hub = PrimeHub()

left_motor  = Motor(Port.A, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.E, Direction.CLOCKWISE)
RAM = Motor(Port.C)   # Right Attachment Motor
LAM = Motor(Port.B)   # Left Attachment Motor


# ─────────────────────────────────────────────
# FACTORY FUNCTION
# ─────────────────────────────────────────────
def make_robot(axle_track=AXLE_TRACK_MM):
    """
    Creates and returns a DriveBase configured for this robot.

    Call once at the very top of each run file (before robot.settings):
        robot = make_robot()            # 122 mm — most runs
        robot = make_robot(101.6)       # Run_A_updated
        robot = make_robot(152)         # Run_D

    This function calls robot.reset() internally, which is the correct
    way to zero the gyro heading in Pybricks v3.6+. Do NOT call
    hub.imu.reset_heading() anywhere in your run files.

    Args:
        axle_track (mm): distance between the two wheel ground contact
                         points. Default 122 mm.
    Returns:
        DriveBase — ready to use, gyro enabled, heading zeroed.
    """
    robot = DriveBase(left_motor, right_motor, WHEEL_DIAMETER_MM, axle_track)
    robot.use_gyro(True)
    robot.reset()   # safe gyro + distance reset — required in Pybricks v3.6+
    return robot


# ─────────────────────────────────────────────
# PID TUNING REFERENCE
# distance_control and heading_control have the same methods as Motor control.
#
# DISTANCE CONTROL — accuracy of straight moves
#   kp: position error gain. Increase if robot consistently stops short.
#   ki: accumulated error gain. Increase if robot never quite reaches target.
#   kd: speed error gain. Increase if robot oscillates or overshoots at end.
#
# HEADING CONTROL — how straight the robot drives
#   kp: Increase if robot drifts. Too high = weaving.
#   ki: Removes persistent left/right heading bias. Keep small.
#   kd: Prevents overcorrection. Increase if robot swings side to side.
#
# Example (add to run file after make_robot()):
#   robot.distance_control.pid(kp=2000, ki=100, kd=200)
#   robot.heading_control.pid(kp=1400, ki=60, kd=500)
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# CALIBRATION GUIDE (from official docs)
#
# STEP 1 — WHEEL DIAMETER (do this first):
#   robot.straight(1000)
#   Measure actual distance traveled.
#   Adjust: new = old * (1000 / actual_distance)
#
# STEP 2 — AXLE TRACK (after wheel diameter is correct):
#   robot.turn(360)
#   Robot should face same direction.
#     Turned too little → increase AXLE_TRACK_MM
#     Turned too far    → decrease AXLE_TRACK_MM
#
# STEP 3 — HEADING PID (if robot drifts while driving straight):
#   Increase heading_control kp in small steps. If it weaves, increase kd.
#
# STEP 4 — LAST MOVE IN A RUN:
#   Use then=Stop.COAST on your final straight/turn so the robot doesn't
#   actively hold position after stopping.
# ─────────────────────────────────────────────
