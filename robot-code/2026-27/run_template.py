# run_template.py -- starting point for a mission file that USES robot_master.py.
# robot_master.py must be in the same Pybricks project. This file only imports what it needs.
# Copy this file for each run (run_1.py, run_2.py, ...) and edit the missions below.
from pybricks.tools import wait
from robot_master import make_drive, make_arm

ENABLE_MOTION = True  # False: only checks the import and prints. True: lets the robot move.


def setup():
    # Builds the drive and the left arm. Keep the robot still for the gyro zero.
    drive = make_drive()
    left_arm = make_arm("left_arm")
    return drive, left_arm


def mission_1(drive, left_arm):
    # Example mission: out to a spot, raise the left arm, then come back. Edit freely.
    # drive.straight(100)  # mm forward
    # drive.turn(90)  # degrees clockwise
    # drive.straight(150)
    left_arm.move_to(150)  # left arm up to 150 arm degrees
    # wait(300)
    # left_arm.move_to(8)  # left arm back down, 8 arm degrees off the stop
    drive.straight(150)
    drive.turn(90)
    # drive.turn(-90)
    # drive.straight(-300)  # back where we started


def main():
    print("robot_master imports OK")
    if not ENABLE_MOTION:
        print("ENABLE_MOTION is False: not moving.")
        return
    drive, left_arm = setup()
    if not left_arm.home_and_park():
        print("Lift homing failed: stopping before any mission.")
        return
    mission_1(drive, left_arm)
    left_arm.release()
    print("DONE, heading error", drive.error())


main()
