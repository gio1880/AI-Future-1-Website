from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.tools import StopWatch, wait

# --------------------
# Hardware setup
# --------------------
hub = PrimeHub()

left_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.E, Direction.CLOCKWISE)

hub.imu.reset_heading(0)

# --------------------
# Kp-only controller
# --------------------
class KpController:
    def __init__(self, kp):
        self.kp = kp

    def compute(self, error):
        return self.kp * error

# --------------------
# Drive straight using IMU correction
# --------------------
def drive_straight_kp(base_speed, duration_ms, controller):
    hub.imu.reset_heading(0)
    timer = StopWatch()

    while timer.time() < duration_ms:
        error = hub.imu.heading()
        correction = controller.compute(error)

        left_motor.run(base_speed - correction)
        right_motor.run(base_speed + correction)

        wait(10)

    left_motor.stop()
    right_motor.stop()

# --------------------
# TEST PARAMETERS
# --------------------
kp = 12         # <-- CHANGE THIS VALUE ONLY
base_speed = 300  # deg/s
duration = 2000   # ms

controller = KpController(kp)

# --------------------
# RUN TEST
# --------------------
drive_straight_kp(base_speed, duration, controller)
