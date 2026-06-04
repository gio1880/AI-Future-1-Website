from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.parameters import Port,Direction,Stop

hub = PrimeHub()
left_motor = Motor(Port.A,Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.E,Direction.CLOCKWISE)
RAM = Motor(Port.C)
LAM = Motor(Port.B)
 
wheel_diameter = 56
axle_track = 101.6
robot = DriveBase(left_motor,right_motor,wheel_diameter,axle_track)

robot.use_gyro(True)

left_motor.control.limits(speed=800)
right_motor.control.limits(speed=800)

hub.imu.reset_heading(0)
hub.imu.ready()


# robot.use_gyro(True)
robot.settings(
    straight_speed=800,
    straight_acceleration=700,
    turn_rate=520,
    turn_acceleration=450
)

robot.heading_control.pid(21242, 0, 5310, 4, 8)



if hub.imu.ready():
    print(robot.heading_control.pid())

    robot.straight(690)
    robot.turn(45)
    print(hub.imu.heading())
    robot.straight(23)
    LAM.run_time(-600,900)
    robot.straight(-40)
    RAM.run_time(-500,1300)
    robot.straight(150)
    RAM.run_time(500,1500)
    robot.straight(-150)
    robot.turn(-45)
    LAM.run_time(600,900)
    robot.straight(110)
    LAM.run_time(-600,600)
    robot.settings(straight_speed = 820,straight_acceleration= 800, turn_rate=600, turn_acceleration=600)
    robot.straight(-200)
    robot.turn(-25,then=Stop.NONE)
    robot.straight(-600,then=Stop.NONE)