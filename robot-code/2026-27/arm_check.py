# arm_check.py -- repeats the left arm moves used in missions, so the dashboard can show how close it lands.
# Run it 2-3 times after any arm tuning change; the dashboard groups the tries under "Arm check".
# The robot does not drive. Each move also prints SETTLED: where the arm is 0.8 s later, to compare with
# the angle logged when the move counted as done.
from robot import *
import robot

left_arm.homing(True)
right_arm.homing(False)
start("Arm check")

arm = robot._arms["left_arm"]
for speed in (100, 60):
    for target in (90, 30, 90, 8, 60, 8):
        left_arm(target, speed)
        done_at = arm.angle()
        pause(800)
        print("SETTLED left_arm", target, "| at done", round(done_at, 1), "| 0.8 s later", round(arm.angle(), 1),
              "| speed", speed)

finish()
