
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Stop

hub = PrimeHub()
attach_motor = Motor(Port.E)

# Motor degrees per output degree
GEAR_RATIO = 0.6

# Verify the physical positive direction.
OUTPUT_SIGN = 1

DEFAULT_PID = attach_motor.control.pid()

PROFILES = {
    "A": {
        "speed": 150,
        "accel": 300,
        "home": 0
    },
    "B": {
        "speed": 100,
        "accel": 200,
        "home": 0
    },
    "C": {
        "speed": 75,
        "accel": 150,
        "home": 0
    }
}

current_profile = None


def select_attachment(name):
    global current_profile

    config = PROFILES[name]

    attach_motor.stop()
    attach_motor.control.pid(*DEFAULT_PID)

    attach_motor.control.limits(
        speed=config["speed"],
        acceleration=config["accel"]
    )

    current_profile = name

    print("Selected attachment:", name)


def move_to(output_angle):
    if current_profile is None:
        print("Select an attachment first")
        return

    config = PROFILES[current_profile]

    target = round(
        output_angle * GEAR_RATIO * OUTPUT_SIGN
    )

    attach_motor.run_target(
        config["speed"],
        target,
        then=Stop.HOLD,
        wait=True
    )


def set_home():
    # Use only after physically aligning the attachment
    # to the agreed zero orientation.
    attach_motor.reset_angle(0)


# Example:
# Align attachment A before running.
select_attachment("A")
set_home()
move_to(30)
