from robot_base import hub, RAM, LAM, make_robot
from pybricks.tools import multitask, run_task, wait
from pybricks.parameters import Stop

robot = make_robot()
robot.settings(straight_speed=520, straight_acceleration=200, turn_rate=200, turn_acceleration=200)

async def main():
        if hub.imu.ready():
                await(robot.straight(560))
                await(robot.straight(-690))


        # await RAM.run_time(-900,800)
        # await robot.straight(400)
        # await robot.turn(-4)
        # await RAM.run_time(1000,500)
        # await RAM.run_time(-1000,900)
        # await RAM.run_time(1000,500)
        # await RAM.run_time(-1000,900)
        # await RAM.run_time(1000,500)
        # await RAM.run_time(-1000,900)
        # await robot.straight(-9999)



# Runs the main program from start to finish.
run_task(main())
