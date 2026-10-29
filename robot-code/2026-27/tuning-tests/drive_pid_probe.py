print("START")
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.robotics import DriveBase
from pybricks.parameters import Port, Direction
print("IMPORTS")
hub = PrimeHub()
print("HUB")
left_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
print("LEFT")
right_motor = Motor(Port.E, Direction.CLOCKWISE)
print("RIGHT")
robot = DriveBase(left_motor, right_motor, 56, 122)
print("DRIVEBASE")
print("GYRO_READY", hub.imu.ready())
robot.use_gyro(True)
print("GYRO_SET")
print("SETTINGS", robot.settings())
print("DIST_PID", robot.distance_control.pid())
print("HEAD_PID", robot.heading_control.pid())

