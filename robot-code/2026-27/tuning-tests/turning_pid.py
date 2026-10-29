from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Stop
from pybricks.tools import wait
# import math

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
def drive_distance(
    distance_mm,
    wheel_diameter_mm,
    heading_controller,
    max_speed=500,
    distance_kp=2.0,
    distance_kd=0.3,
    feedforward=100,
    min_speed=50,
    tolerance_deg=2,
    feedforward_cutoff=50
):
    """
    Drives a set distance in mm while keeping heading straight.
    Adaptive feedforward reduces oscillation near target.
    """
    # Target motor rotation
    wheel_circ = 3.14 * wheel_diameter_mm
    target_deg = (distance_mm / wheel_circ) * 360

    # Reset sensors
    left_motor.reset_angle(0)
    right_motor.reset_angle(0)
    hub.imu.reset_heading(0)
    heading_controller.reset()

    # Distance PD variables
    last_distance_error = 0

    print("Starting drive for {} mm → {:.2f} deg rotation".format(distance_mm, target_deg))

    while True:
        # Average motor angle
        current_deg = (left_motor.angle() + right_motor.angle()) / 2
        distance_error = target_deg - current_deg

        # Stop if within tolerance
        if abs(distance_error) <= tolerance_deg:
            break

        # Adaptive feedforward: only apply if far from target
        if abs(distance_error) < feedforward_cutoff:
            ff = 0
        else:
            ff = feedforward

        # Distance PD
        distance_derivative = distance_error - last_distance_error
        last_distance_error = distance_error

        base_speed = ff + distance_kp * distance_error + distance_kd * distance_derivative

        # Clamp base speed to min/max
        if base_speed > 0:
            base_speed = max(min_speed, min(max_speed, base_speed))
        else:
            base_speed = min(-min_speed, max(-max_speed, base_speed))

        # Heading correction
        heading_error = hub.imu.heading()
        correction = heading_controller.compute(heading_error)

        # Motor speeds
        left_speed = base_speed - correction
        right_speed = base_speed + correction

        # Run motors
        left_motor.run(left_speed)
        right_motor.run(right_speed)

        # Print monitoring info
        print(
            "H: {:.2f} | L_angle: {:.2f} R_angle: {:.2f} | L_speed: {:.2f} R_speed: {:.2f}".format(
                heading_error,
                left_motor.angle(),
                right_motor.angle(),
                left_speed,
                right_speed
            )
        )

        wait(10)  # ~100 Hz loop

    # Stop motors
    left_motor.stop()
    right_motor.stop()
    print("Drive finished.")

def turn_to_heading(target_heading, heading_controller, max_speed=200, tolerance_deg=1):
    """
    Turns robot to a specific IMU heading using velocity PD control.
    """
    heading_controller.reset()
    print(f"Starting turn to {target_heading:.2f} deg")

    while True:
        current_heading = -hub.imu.heading()
        # Compute shortest error
        error = (target_heading - current_heading)

        # Stop if within tolerance
        if abs(error) <= tolerance_deg:
            break

        # PD control
        correction = heading_controller.compute(error)

        # Clamp to max_speed
        motor_speed = max(-max_speed, min(max_speed, correction))

        left_motor.run(-motor_speed)
        right_motor.run(motor_speed)

        print(f"Target: {target_heading:.2f} | H: {current_heading:.2f} | Error: {error:.2f} | Speed: {motor_speed:.2f}")
        wait(20)  # slower loop to reduce overshoot

    left_motor.stop()
    right_motor.stop()
    print(f"Turn finished to {target_heading:.2f} deg")

# --------------------
# Tuning values
# --------------------
Kp_heading = 12.0
Kd_heading = 0.8
heading_controller = PDController(Kp_heading, Kd_heading)

wheel_diameter = 56  # mm, adjust to your wheels

# --------------------
# RUN TEST
# --------------------
# drive_distance(
#     distance_mm=500,
#     wheel_diameter_mm=wheel_diameter,
#     heading_controller=heading_controller,
#     max_speed=500,
#     distance_kp=2.5,
#     distance_kd=0.3,
#     feedforward=100,
#     min_speed=60,
#     tolerance_deg=2,
#     feedforward_cutoff=50
# )
turn_to_heading(-90, heading_controller)
