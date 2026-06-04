from robot_base import hub, RAM, LAM, make_robot
from pybricks.tools import multitask, run_task, wait
from pybricks.parameters import Stop

robot = make_robot()
robot.settings(straight_speed=720, straight_acceleration=400, turn_rate=600, turn_acceleration=400)

async def main():
   if hub.imu.ready():
      print(robot.heading_control.pid())
      # LAM.run_time(-1000,1400)
      await robot.straight(225)
      await robot.turn(-46)
      await LAM.run_time(-300,800)
      await robot.straight(208)
      await LAM.run_time(-300,800)
      await RAM.run_time(-1300,1150)
      await LAM.run_time(700,780)
      await LAM.run_time(-700,800)
      await robot.straight(-215)
      await RAM.run_time(1000,1300,then=Stop.HOLD)
      robot.settings(straight_speed=950, straight_acceleration=800, turn_rate=700, turn_acceleration=750)

      # await robot.straight(70,then=Stop.HOLD)
      await robot.turn(-25,Stop.NONE)
      # await robot.turn(35)
      await robot.straight(-500)




# Runs the main program from start to finish.
run_task(main())
