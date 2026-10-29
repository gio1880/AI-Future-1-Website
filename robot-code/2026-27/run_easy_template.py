# run_easy_template.py -- copy this for each run, rename the copy (run_1.py, run_2.py, ...), then edit the moves.
# Needs robot.py and robot_master.py in the same Pybricks project. All commands are listed at the top of robot.py.
#   drive(+) forward   drive(-) backward   turn(+) right   turn(-) left
#   speed is a percent: drive(150, 40) = this move at 40%.  set_speed(50) = every move after it at 50%.
#   arms: left_arm = port B, right_arm = port F.  left_arm(90) go to 90.  left_arm.by(-20) down 20.  wait=False = don't wait for it.
from robot import *

# ---- SETUP (before start) ----
gears(left=[20, [12, 12], 12])  # gears on each arm, MOTOR first. Add right=[...] once the right arm is on.
left_arm.homing(True)  # True = lower onto its stop at start.  False = nothing mounted / no stop
right_arm.homing(True)  # goes down to its stop and back to its start position (0). False = nothing mounted
robot_homing(False)  # True = back gently into the wall behind the robot at start to line it up
arm_speed(left_up=100, left_down=60)  # raise at full speed, lower a bit slower

start("Run 1")  # hands off the robot! The name is what the dashboard shows.

# ---- your moves (example: out fast, slow near the model, back fast) ----
left_arm(90, wait=False)  # left arm goes up WHILE the robot drives out
drive(300)
turn(90)
wait_for_arms()  # make sure the left arm is up before going in
drive(150, 40)  # slow and careful into the model
left_arm(30, 50)  # left arm down at half speed
left_arm.by(20)  # then 20 back up
drive(-150)
turn(-90)
drive(-300)

finish()
