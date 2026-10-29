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
# Distance-based drive
# --------------------
def drive_distance(distance_mm, wheel_diameter_mm, heading_controller, 
                   max_speed, distance_kp=1.0, distance_kd=0.0, tolerance_deg=2):
    """
    Drives a set distance in mm while keeping heading straight.
    """
    # Calculate target motor rotation
    wheel_circ = 3.14 * wheel_diameter_mm
    target_deg = (distance_mm / wheel_circ) * 360

    # Reset sensors
    left_motor.reset_angle(0)
    right_motor.reset_angle(0)
    hub.imu.reset_heading(0)
    heading_controller.reset()

    # PD variables for distance
    last_distance_error = 0

    print(f"Starting drive for {distance_mm} mm → {target_deg:.2f} deg rotation")

    while True:
        # Average motor angle
        current_deg = (left_motor.angle() + right_motor.angle()) / 2
        distance_error = target_deg - current_deg

        # Check if within tolerance
        if abs(distance_error) <= tolerance_deg:
            break

        # Distance PD (simple P + optional D)
        distance_derivative = distance_error - last_distance_error
        last_distance_error = distance_error
        base_speed = distance_kp * distance_error + distance_kd * distance_derivative

        # Clamp base speed to max
        base_speed = max(-max_speed, min(max_speed, base_speed))

        # Heading correction
        heading_error = hub.imu.heading()
        correction = heading_controller.compute(heading_error)

        # Compute motor speeds
        left_speed = base_speed - correction
        right_speed = base_speed + correction

        # Run motors
        left_motor.run(left_speed)
        right_motor.run(right_speed)

        # Print for monitoring
        # print(f"H: {heading_error:.2f} | L_angle: {left_motor.angle():.2f} "
        #       f"R_angle: {right_motor.angle():.2f} | L_speed: {left_speed:.2f} "
        #       f"R_speed: {right_speed:.2f}")

        wait(10)  # ~100 Hz loop

    left_motor.stop()
    right_motor.stop()
    print("Drive finished.")

# --------------------
# Tuning values
# --------------------
Kp_heading = 12.0
Kd_heading = 0.8

max_speed = 500            # deg/s max
wheel_diameter = 56        # mm, change to your wheel
heading_controller = PDController(Kp_heading, Kd_heading)

# Optional: distance PD tuning
distance_kp = 1.5
distance_kd = 0.0

# --------------------
# RUN TEST
# --------------------
drive_distance(
    distance_mm=500,
    wheel_diameter_mm=wheel_diameter,
    heading_controller=heading_controller,
    max_speed=max_speed,
    distance_kp=distance_kp,
    distance_kd=distance_kd,
    tolerance_deg=2
)
