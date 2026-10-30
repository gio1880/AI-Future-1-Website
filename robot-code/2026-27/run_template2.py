# run_template.py -- starting point for a mission file that USES robot_master.py.
# robot_master.py must be in the same Pybricks project. This file only imports what it needs.
# Copy this file for each run (run_1.py, run_2.py, ...) and edit the missions below.
# Both attachment arms are built here: arms["left_arm"] (port B) and arms["right_arm"] (port F).
from pybricks.tools import wait
from robot_master import make_drive, make_arms, home_arms

ENABLE_MOTION = True  # False: only checks the import and prints. True: lets the robot move.
ENABLE_RIGHT_ARM = False  # True once an attachment is mounted on port F and its settings are in robot_master.py


def setup():
    # Builds the drive and BOTH arms. Keep the robot still for the gyro zero.
    drive = make_drive()
    arms = make_arms()  # {"left_arm": Arm on port B, "right_arm": Arm on port F}
    return drive, arms


def mission_1(drive, arms):
    # Example mission: out to a spot, move the arms, then come back. Edit freely.
    left_arm = arms["left_arm"]
    right_arm = arms["right_arm"]
    drive.straight(100)  # mm forward
    drive.turn(90)  # degrees clockwise
    drive.straight(150)
    left_arm.move_to(150)  # left arm up to 150 arm degrees
    

def main():
    print("robot_master imports OK")
    if not ENABLE_MOTION:
        print("ENABLE_MOTION is False: not moving.")
        return
    drive, arms = setup()
    # Stall-homes every arm with home=True (the left arm); arms with home=False are zeroed in place (right arm).
    if not home_arms(arms):
        print("Arm homing failed: stopping before any mission.")
        return
    mission_1(drive, arms)
    for name in arms:
        arms[name].release()
    print("DONE, heading error", drive.error())


main()
