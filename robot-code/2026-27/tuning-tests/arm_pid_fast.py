from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Stop
from pybricks.tools import StopWatch


attach_motor = Motor(Port.E)

# Motor degrees per output degree. Check this against the real gearing.
GEAR_RATIO = 0.6
OUTPUT_SIGN = 1

# Keep the motor's calibrated PID gains. Tune them only after measuring a move.
DEFAULT_PID = attach_motor.control.pid()

# Speed is in motor deg/s; acceleration is in motor deg/s^2.
# These are starting points, not measured limits for your attachments.
PROFILES = {
    "A": {"speed": 300, "accel": 900},
    "B": {"speed": 220, "accel": 600},
    "C": {"speed": 150, "accel": 400},
}

current_profile = None


def select_attachment(name):
    global current_profile
    config = PROFILES[name]
    attach_motor.stop()
    attach_motor.control.pid(*DEFAULT_PID)
    attach_motor.control.limits(
        speed=config["speed"],
        acceleration=config["accel"],
    )
    current_profile = name
    print("Attachment:", name, "PID:", attach_motor.control.pid())


def set_home():
    # Align the attachment at its agreed zero position first.
    attach_motor.reset_angle(0)


def move_to(output_angle):
    if current_profile is None:
        raise ValueError("Select an attachment first")

    target = round(output_angle * GEAR_RATIO * OUTPUT_SIGN)
    watch = StopWatch()
    attach_motor.run_target(
        PROFILES[current_profile]["speed"],
        target,
        then=Stop.HOLD,
        wait=True,
    )
    actual = attach_motor.angle()
    error = target - actual
    elapsed_ms = watch.time()
    print("Target:", target, "Actual:", actual,
          "Error:", error, "Time ms:", elapsed_ms)
    return elapsed_ms, error


# Test only after checking clearance and aligning the attachment:
# select_attachment("A")
# set_home()
# move_to(30)

