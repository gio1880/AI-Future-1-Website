from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.parameters import Port,Direction
from pybricks.tools import multitask, run_task, wait


hub = PrimeHub()
left_motor = Motor(Port.A,Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.E,Direction.CLOCKWISE)
RAM = Motor(Port.C)
LAM = Motor(Port.B)

wheel_diameter = 56
axle_track = 122
robot = DriveBase(left_motor,right_motor,wheel_diameter,axle_track)

robot.use_gyro(True)
robot.settings(straight_speed = 720,straight_acceleration= 400, turn_rate=600, turn_acceleration=400)
hub.imu.reset_heading(0)

async def main():
   if hub.imu.ready():
      print(robot.heading_control.pid())
      robot.settings(straight_speed = 720,straight_acceleration= 400, turn_rate=600, turn_acceleration=400)

      await robot.straight(325) 
      await RAM.run_time(-1000,-1400)
      await robot.straight(-300)
      await RAM.run_time(-1000,-400)
      await robot.straight(-10000)
      

# Runs the main program from start to finish.
run_task(main())
