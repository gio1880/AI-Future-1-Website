from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.tools import StopWatch, wait

# --------------------
# Hardware setup
# --------------------
hub = PrimeHub()

left_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.E)

hub.imu.reset_heading(0)

# --------------------
# PD Controller
# --------------------
class PDController:
    def __init__(self, kp, kd):
        self.kp = kp
        self.kd = kd
        self.last_error = 0

    def compute(self, error):
        derivative = error - self.last_error
        self.last_error = error
        return self.kp * error + self.kd * derivative

# --------------------
# Drive straight with IMU correction
# --------------------
def drive_straight_pd(base_speed, duration_ms, controller):
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
# TUNING VALUES
# --------------------
Kp = 12.0        # 🔒 LOCKED
Kd = 0.8        # <-- CHANGE ONLY THIS

base_speed = 800
duration = 3000

controller = PDController(Kp, Kd)

# --------------------
# RUN TEST
# --------------------
drive_straight_pd(base_speed, duration, controller)
