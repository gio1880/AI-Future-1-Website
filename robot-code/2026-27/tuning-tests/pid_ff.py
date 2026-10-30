from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Stop
from pybricks.tools import StopWatch, wait

# --------------------
# Hardware setup
# --------------------
hub = PrimeHub()

left_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.E)

hub.imu.reset_heading(0)

# --------------------
# PD Controller for heading correction
# --------------------
class PDController:
    def __init__(self, kp, kd):
        self.kp = kp
        self.kd = kd
        self.last_error = 0

    def reset(self):
        self.last_error = 0

    def compute(self, error):
        derivative = error - self.last_error
        self.last_error = error
        return self.kp * error + self.kd * derivative

# --------------------
# Drive straight with velocity control + PD heading
# --------------------
def drive_straight_velocity_pd(target_speed, duration_ms, controller):
    """
    target_speed: deg/s (positive forward)
    duration_ms: duration of motion
    controller: PDController instance
    """
    hub.imu.reset_heading(0)
    controller.reset()
    timer = StopWatch()

    print("Starting drive...")
    while timer.time() < duration_ms:
        # ------------------------
        # Heading error
        # ------------------------
        heading = hub.imu.heading()
        correction = controller.compute(heading)

        # ------------------------
        # Compute motor velocities
        # ------------------------
        left_speed = target_speed - correction
        right_speed = target_speed + correction

        # ------------------------
        # Command motors in deg/s
        # ------------------------
        left_motor.run(left_speed)
        right_motor.run(right_speed)

        # ------------------------
        # Print for monitoring
        # ------------------------
        print(f"H: {heading:.2f} deg | L: {left_speed:.2f} | R: {right_speed:.2f}")

        wait(10)  # ~100 Hz loop

    left_motor.stop()
    right_motor.stop()
    print("Drive finished.")

# --------------------
# PD Tuning values
# --------------------
Kp = 12.0
Kd = 0.8

target_speed = 300  # deg/s
duration = 3000     # ms

controller = PDController(Kp, Kd)

# --------------------
# RUN TEST
# --------------------
drive_straight_velocity_pd(target_speed, duration, controller)
