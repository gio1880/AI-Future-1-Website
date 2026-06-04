from robot_base import hub, RAM, LAM, make_robot
from pybricks.tools import multitask, run_task, wait
from pybricks.parameters import Stop

robot = make_robot()
robot.settings(straight_speed=320, straight_acceleration=400, turn_rate=200, turn_acceleration=200)

async def main():
   if hub.imu.ready():
        print(robot.heading_control.pid())
        await robot.straight(710,then=Stop.HOLD)
        # robot.settings(straight_speed=320, straight_acceleration=100, turn_rate=200, turn_acceleration=200)
        # await robot.straight(10,then=Stop.HOLD)
        # await robot.straight(180)
        await RAM.run_time(700,600)
        # await RAM.run_time(-700,800)

        # await robot.straight(-15)

        # await RAM.run_time(-500,1050)
        await robot.straight(-900)

        # await multitask(RAM.run_time(-500,500),robot.straight(-600))


# Runs the main program from start to finish.
run_task(main())
