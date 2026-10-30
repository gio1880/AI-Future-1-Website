from robot import *

gears(left=[20, [12, 12], 12])  # gears on each arm, MOTOR first. Add right=[...] once the right arm is on.
gears(right=[20, [12, 12], 12])  # gears on each arm, MOTOR first. Add right=[...] once the right arm is on.

left_arm.homing(True)
right_arm.homing(True)

start("RUN A")  # hands off the robot!

# ---- your moves (example: out fast, slow near the model, back fast) ----
drive(700,80)
left_arm(90)
right_arm(-58)  # arm degrees now (was -35 before the right arm's gears were recorded - same spot)
turn(-8)
drive(145,40)
turn(15)
drive(-10,30)
right_arm(-150,100)  # was -90 before the gears were recorded - same spot



finish()
