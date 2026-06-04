from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.tools import wait

# Create motors (START with all set the same)
front_left  = Motor(Port.A, Direction.CLOCKWISE)
front_right = Motor(Port.B, Direction.COUNTERCLOCKWISE)
back_left   = Motor(Port.C, Direction.CLOCKWISE)
back_right  = Motor(Port.D, Direction.COUNTERCLOCKWISE)

SPEED = 300
TIME = 2000  # milliseconds
def drive(speed):
    front_left.run(speed)
    front_right.run(speed)
    back_left.run(speed)
    back_right.run(speed)
def turn(speed):
    front_left.run(speed)
    back_left.run(speed)

    front_right.run(-speed)
    back_right.run(-speed)
def stop():
    front_left.stop()
    front_right.stop()
    back_left.stop()
    back_right.stop()

drive(400)
wait(2000)

turn(3000)
wait(1000)

drive(-400)
wait(2000)

stop()
