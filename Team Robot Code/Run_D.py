from robot_base import hub, RAM, LAM, make_robot
from pybricks.tools import multitask, run_task, wait
from pybricks.parameters import Stop

# Run_D uses axle_track=152 — passed directly to make_robot().
# make_robot() calls robot.reset() internally (safe Pybricks v3.6+ way).
robot = make_robot(axle_track=152)
robot.settings(straight_speed=450, straight_acceleration=200, turn_rate=300, turn_acceleration=300)
# robot.heading_control.pid(kp=1000,ki=100,kd=200)

#Run D completes mission 3 and 4.
async def main():
   if hub.imu.ready():
        await robot.straight(-900, then=Stop.HOLD)

        await robot.straight(34)
        await robot.turn(-92)
        await RAM.run_time(-500,690)  # lower the arm for minecart

        

        await LAM.run_time(520,520)   # opening arm for artifact

        await robot.straight(165)
        await robot.straight(-12)

        await LAM.run_time(-500,740)  # clamp the artifact
        await RAM.run_time(200,1000)  # raise the arm for minecart

        await wait(500)
        await RAM.run_time(-500,300)

        robot.settings(straight_speed=850, straight_acceleration=600, turn_rate=300, turn_acceleration=300)

        await robot.straight(-155)
        await robot.turn(100, then=Stop.NONE)
        await robot.straight(1000, then=Stop.NONE)


# Runs the main program from start to finish.
run_task(main())
