from robot_base import hub, RAM, LAM, make_robot
from pybricks.tools import multitask, run_task, wait
from pybricks.parameters import Stop

robot = make_robot()
robot.settings(straight_speed=820, straight_acceleration=550, turn_rate=600, turn_acceleration=400)

if hub.imu.ready():

    robot.straight(350, then=Stop.HOLD)
    robot.straight(350, then=Stop.HOLD)
    robot.straight(-200, then=Stop.HOLD)
    robot.straight(139, then=Stop.HOLD)
    robot.straight(-43)
    LAM.run_time(1200,1400)
    # wait(500)
    # LAM.run_time(500,1400)
    robot.straight(-150)
    robot.turn(35)
    robot.straight(180)
    robot.turn(-67, then=Stop.HOLD)
    robot.straight(240, then=Stop.HOLD)
    RAM.run_time(-500,800)
    robot.settings(straight_speed=820, straight_acceleration=400, turn_rate=600, turn_acceleration=400)


    robot.straight(-150, then=Stop.NONE)
    robot.turn(25, then=Stop.NONE)
    robot.straight(-800, then=Stop.NONE)
