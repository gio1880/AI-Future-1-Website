# mission_4_5_debug.py -- runs the SAME moves as mission_4_5 and logs drift, turn error and wheel slip.
# It waits for the LEFT hub button so you control when it starts (place the robot first).
# Output lines: step | planned | dist (encoders, mm) | gyroDH (gyro heading change) | encDH (wheel-implied)
#               | err (gyro minus target heading) | ms
from pybricks.hubs import PrimeHub
from pybricks.parameters import Axis, Button
from pybricks.tools import wait, StopWatch
from umath import pi, sin, cos
from robot_master import make_drive, make_arms, home_arms, TW, WHEEL_MM

hub = PrimeHub()
DPM = 360 / (pi * WHEEL_MM)

print("READY: place the robot, then press the LEFT hub button")
while Button.LEFT not in hub.buttons.pressed():
    wait(20)
while Button.LEFT in hub.buttons.pressed():
    wait(20)
wait(1500)  # let the robot settle after your hand leaves it

mx = 0
for i in range(15):
    v = abs(hub.imu.angular_velocity(Axis.Z))
    if v > mx:
        mx = v
    wait(20)
print("START battery_mV", hub.battery.voltage(), "max_turn_rate_before_zero_deg_s", round(mx, 2))

drive = make_drive(hub)  # run 7: NO overrides, uses the robot_master.py settings only
arms = make_arms()
total = StopWatch()
sw = StopWatch()
ok = home_arms(arms)
print("HOME ok", ok, "ms", sw.time())
if not ok:
    raise SystemExit
left_arm = arms["left_arm"]
X = 0.0
Y = 0.0


def rec(label, plan, fn, kind):
    global X, Y
    h0 = hub.imu.heading()
    l0 = drive.l.angle()
    r0 = drive.r.angle()
    t = StopWatch()
    fn(plan)
    ms = t.time()
    h1 = hub.imu.heading()
    l1 = drive.l.angle()
    r1 = drive.r.angle()
    if kind == "S":
        dl = l1
        dr = r1
    else:
        dl = l1 - l0
        dr = r1 - r0
    dist = (dl + dr) / 2 / DPM
    enc_dh = (dl - dr) / 2 / TW
    if kind == "S":
        hm = (h0 + h1) / 2 * pi / 180
        X += dist * sin(hm)
        Y += dist * cos(hm)
    print(label, plan, "| dist", round(dist, 1), "| gyroDH", round(h1 - h0, 2), "| encDH", round(enc_dh, 2),
          "| err", round(drive.error(), 2), "| ms", ms)


def lrec(label, target):
    t = StopWatch()
    left_arm.move_to(target)
    print(label, target, "| angle", round(left_arm.angle(), 1), "| err", round(left_arm.error_to(target), 1),
          "| ms", t.time(), "| load", left_arm.load())


lrec("1 LEFT ARM", 150)  # arm degrees (was 90 motor degrees, same spot)
rec("2 STRAIGHT", 100, drive.straight, "S")
rec("3 TURN", 25, drive.turn, "T")
rec("4 STRAIGHT", 570, drive.straight, "S")
rec("5 TURN", -67, drive.turn, "T")
lrec("6 LEFT ARM", 55)  # was 33 motor degrees
rec("7 STRAIGHT", 230, drive.straight, "S")
lrec("8 LEFT ARM", 108)  # was 65 motor degrees
rec("9 STRAIGHT", -100, drive.straight, "S")
print("END heading_err", round(drive.error(), 2), "xy_est_mm", round(X, 1), round(Y, 1),
      "total_ms", total.time(), "battery_mV", hub.battery.voltage())
for name in arms:
    arms[name].release()
print("DONE")
