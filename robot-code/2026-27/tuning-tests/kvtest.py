from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Stop
from pybricks.tools import wait

hub = PrimeHub()

left = Motor(Port.A)
right = Motor(Port.E)

kS = 0.18   # <-- use your measured kS
test_powers = [0.30, 0.40, 0.50]

print("Starting kV test...")

for power in test_powers:
    left.reset_angle(0)
    right.reset_angle(0)

    left.dc(power * 100)
    right.dc(power * 100)

    wait(2000)  # let speed settle

    l_speed = abs(left.speed())   # deg/s
    r_speed = abs(right.speed())

    avg_speed = (l_speed + r_speed) / 2

    print("Power:", power,
          "Speed (deg/s):", int(avg_speed))

    left.stop()
    right.stop()
    wait(1000)
