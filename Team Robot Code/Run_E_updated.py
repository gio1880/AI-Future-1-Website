from robot_base import hub, RAM, LAM, make_robot
from pybricks.tools import multitask, run_task, wait
from pybricks.parameters import Stop

robot = make_robot()
robot.settings(straight_speed=520, straight_acceleration=200, turn_rate=200, turn_acceleration=200)

#Run E completes mission 11 and 13. transition from blue to red.
async def main():
   if hub.imu.ready():
        await robot.straight(550,then=Stop.HOLD)
        # await robot.turn(-87,then=Stop.HOLD)
        print(hub.imu.heading())
        # await robot.straight(475,then=Stop.HOLD)
        await robot.turn(-3,then=Stop.HOLD)
        print(hub.imu.heading())
        await robot.straight(65,then=Stop.HOLD)
        await robot.turn(5)
        await LAM.run_time(-1500,1500)
        await robot.straight(-70,then=Stop.HOLD)
        await robot.turn(22)
        await robot.straight(510)
        await RAM.run_time(800,720)
        await robot.turn(20)
        await robot.turn(-15)
        robot.settings(straight_speed=820, straight_acceleration=800, turn_rate=800, turn_acceleration=600)
        await robot.straight(-85,then=Stop.HOLD)
        await robot.turn(-33,then=Stop.NONE)
        print(hub.imu.heading())
        await robot.straight(800,then=Stop.NONE)


# Runs the main program from start to finish.
run_task(main())
