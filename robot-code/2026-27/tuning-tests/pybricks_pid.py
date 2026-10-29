from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.parameters import Port, Direction, Button
from pybricks.tools import wait

# --------------------
# Initialize hardware
# --------------------
hub = PrimeHub()

left_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.E, Direction.CLOCKWISE)

robot = DriveBase(
    left_motor,
    right_motor,
    wheel_diameter=56,
    axle_track=160
)

robot.use_gyro(True)
hub.imu.reset_heading(0)

robot.settings(
    straight_speed=800,
    straight_acceleration=600,
    turn_rate= 600,
    turn_acceleration= 400
)

# --------------------
# PID values
# --------------------
DIST_KP = 1500
DIST_KI = 100
DIST_KD = 200

heading_kp = 1500
heading_ki = 100
heading_kd = 200

# robot.distance_control.pid(
#     kp=DIST_KP,
#     ki=DIST_KI,
#     kd=DIST_KD
# )

robot.heading_control.pid(
    kp=heading_kp,
    ki=heading_ki,
    kd=heading_kd
)

# --------------------
# Motion parameters
# --------------------
DISTANCE = 200  # mm
direction = 1

# Reset encoders
robot.reset()
left_motor.reset_angle(0)
right_motor.reset_angle(0)

# --------------------
# Main loop
# --------------------
while True:

    # ---- Button handling ----
    buttons = hub.buttons.pressed()

    if Button.RIGHT in buttons:
        heading_kp += 100
        robot.heading_control.pid(
            kp=heading_kp,
            ki=heading_ki,
            kd=heading_kd
        )
        wait(200)

    if Button.LEFT in buttons:
        heading_kp = max(0, heading_kp - 100)
        robot.heading_control.pid(
            kp=heading_kp,
            ki=heading_ki,
            kd=heading_kd
        )
        wait(200)

    # ---- Drive command ----
    robot.straight(DISTANCE * direction)
    direction *= -1

    # ---- Telemetry loop (while stopped briefly) ----
    for _ in range(10):
        heading = hub.imu.heading()
        distance = robot.distance()

        motor_deg = (left_motor.angle() + right_motor.angle()) / 2

        print(
            "Heading:", heading,
            "| KP:", heading_kp,
            "| Distance(mm):", distance,
            "| Motor(deg):", motor_deg
        )

        wait(100)
