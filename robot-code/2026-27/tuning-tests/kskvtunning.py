from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Stop
from pybricks.tools import wait

hub = PrimeHub()

left = Motor(Port.A)
right = Motor(Port.E)

# Reset encoders
left.reset_angle(0)
right.reset_angle(0)

print("Starting kS test...")

power = 0.0
step = 0.02   # increase slowly

while power <= 1.0:
    left.dc(power * 100)
    right.dc(power * 100)

    wait(500)

    left_angle = abs(left.angle())
    right_angle = abs(right.angle())

    print("Power:", round(power, 2),
          "Left:", left_angle,
          "Right:", right_angle)

    if left_angle > 5 or right_angle > 5:
        print("Robot started moving!")
        print("Estimated kS =", round(power, 2))
        break

    power += step

left.stop()
right.stop()
