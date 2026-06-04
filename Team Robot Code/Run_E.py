from robot_base import hub, RAM, LAM, make_robot
from pybricks.tools import multitask, run_task, wait
from pybricks.parameters import Stop

robot = make_robot()
robot.settings(straight_speed=820, straight_acceleration=500, turn_rate=600, turn_acceleration=500)

#Run E completes mission 11 and 13. transition from blue to red.
async def main():
   if hub.imu.ready():
        await robot.straight(145,then=Stop.HOLD)
        await robot.turn(-88,then=Stop.HOLD)
        print(hub.imu.heading())
        await robot.straight(475,then=Stop.HOLD)
        await robot.turn(-8,then=Stop.HOLD)
        print(hub.imu.heading())
        await robot.straight(60,then=Stop.HOLD)
        await LAM.run_time(-1500,1500)
        await robot.straight(-100,then=Stop.HOLD)
        await robot.turn(28) #just changed
        await robot.straight(490)
        # await robot.turn(15)
        await RAM.run_time(800,750)
        await robot.turn(-15)
        robot.settings(straight_speed=820, straight_acceleration=800, turn_rate=800, turn_acceleration=600)
        await robot.straight(-45,then=Stop.HOLD)
        await robot.turn(-23,then=Stop.NONE)
        print(hub.imu.heading())
        await robot.straight(800,then=Stop.NONE)


# Runs the main program from start to finish.
run_task(main())
