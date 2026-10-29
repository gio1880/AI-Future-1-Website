from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port
from pybricks.tools import wait, StopWatch

# Diagnostic: does each motor turn freely at slow speed, or is something blocking it?
# 60 deg/s for 2 s each way (max 120 deg), with two torque limits. No stall logic.
hub = PrimeHub()
for nm, port in [("C", Port.C), ("D", Port.D)]:
    m = Motor(port)
    for torque in [50, 100]:
        for d in [1, -1]:
            m.control.limits(speed=60, acceleration=2000, torque=torque)
            m.stop()
            wait(300)
            a0 = m.angle()
            m.run(60 * d)
            angs = []
            spds = []
            lds = []
            st = -1
            sw = StopWatch()
            i = 0
            while sw.time() < 2000:
                wait(200)
                angs.append(m.angle() - a0)
                spds.append(int(m.speed()))
                lds.append(int(m.load()))
                if st < 0 and m.control.stalled():
                    st = i
                i += 1
            m.stop()
            print(nm, "T", torque, "d", d, "ang", angs, "spd", spds, "ld", lds, "stalled@", st)
print("DONE")
