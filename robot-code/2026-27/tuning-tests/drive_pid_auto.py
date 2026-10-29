from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch
from umath import sqrt, pi

# Arena 2ft x 2ft, robot at center -> legs of 120 mm only.
hub = PrimeHub()
lm = Motor(Port.A, Direction.COUNTERCLOCKWISE)
rm = Motor(Port.E, Direction.CLOCKWISE)
WD = 55
TRK = 150
robot = DriveBase(lm, rm, WD, TRK)
robot.use_gyro(True)
hub.imu.reset_heading(0)
BASE = robot.heading_control.pid()
print("BASE_HEAD_PID", BASE)

DPM = 360 / (pi * WD)  # wheel deg per mm
TW = TRK / WD  # wheel deg per body deg (each wheel)
D = 120
PAIRS = 3


def stats(name, drifts, worsts, times):
    n = len(drifts)
    md = sum([abs(x) for x in drifts]) / n
    mw = max([abs(x) for x in worsts])
    mt = sum(times) / n
    print(name, "mean|drift|", round(md, 2), "max|err|", round(mw, 2), "ms", int(mt))


# ---------- built-in DriveBase ----------
def builtin_leg(d, vmax, acc):
    robot.settings(vmax, acc, 300, 1800)
    h0 = hub.imu.heading()
    sw = StopWatch()
    robot.straight(d, wait=False)
    worst = 0
    while not robot.done():
        e = hub.imu.heading() - h0
        if abs(e) > abs(worst):
            worst = e
        wait(5)
    t = sw.time()
    wait(250)
    return hub.imu.heading() - h0, worst, t


def builtin_straight(vmax, acc, m):
    robot.settings(vmax, acc, 300, 1800)
    robot.heading_control.pid(kp=int(BASE[0] * m), kd=int(BASE[2] * m))
    dr = []
    wo = []
    ti = []
    for i in range(PAIRS):
        for d in [D, -D]:
            a, b, c = builtin_leg(d, vmax, acc)
            dr.append(a)
            wo.append(b)
            ti.append(c)
    stats("B-STR v%d a%d kpx%s" % (vmax, acc, m), dr, wo, ti)


def builtin_turn(rate, acc, m):
    robot.settings(300, 1800, rate, acc)
    robot.heading_control.pid(kp=int(BASE[0] * m), kd=int(BASE[2] * m))
    er = []
    ti = []
    for k in range(6):
        s = 90 if k % 2 == 0 else -90
        tgt = hub.imu.heading() + s
        sw = StopWatch()
        robot.turn(s)
        ti.append(sw.time())
        wait(250)
        er.append(hub.imu.heading() - tgt)
    stats("B-TRN r%d a%d kpx%s" % (rate, acc, m), er, er, ti)


# ---------- custom state-feedback controller ----------
def prof(dd, vmax, a):
    if dd >= vmax * vmax / a:
        vp = vmax
        ta = vp / a
        tc = (dd - vp * vp / a) / vp
    else:
        vp = sqrt(a * dd)
        ta = vp / a
        tc = 0
    return vp, ta, tc, 2 * ta + tc


def ref(t, dd, vp, ta, tc, a, T):
    if t >= T:
        return dd, 0
    if t < ta:
        return 0.5 * a * t * t, a * t
    if t < ta + tc:
        return 0.5 * a * ta * ta + vp * (t - ta), vp
    td = T - t
    return dd - 0.5 * a * td * td, a * td


def custom_straight(d, vmax, a, kh, kw, ks):
    sg = 1 if d > 0 else -1
    dd = abs(d)
    vp, ta, tc, T = prof(dd, vmax, a)
    lm.reset_angle(0)
    rm.reset_angle(0)
    h0 = hub.imu.heading()
    hp = 0
    tp = 0
    w = 0
    worst = 0
    sw = StopWatch()
    t = 0
    while t < T * 1000 + 200:
        t = sw.time()
        sr, vr = ref(min(t / 1000, T), dd, vp, ta, tc, a, T)
        s = (lm.angle() + rm.angle()) / 2 / DPM
        h = hub.imu.heading() - h0
        if t > tp:
            w = 0.6 * w + 0.4 * (h - hp) * 1000 / (t - tp)
        hp = h
        tp = t
        if abs(h) > abs(worst):
            worst = h
        if abs(h) > 40 or abs(s) > dd + 60:
            lm.stop()
            rm.stop()
            print('ABORT straight', h, s)
            raise SystemExit
        v = sg * vr + ks * (sg * sr - s)
        c = (-kh * h - kw * w) * TW
        base = v * DPM
        lm.run(base + c)
        rm.run(base - c)
        wait(5)
    lm.hold()
    rm.hold()
    wait(250)
    return hub.imu.heading() - h0, worst, int(T * 1000)


def custom_straight_set(vmax, a, kh, kw, ks):
    dr = []
    wo = []
    ti = []
    for i in range(PAIRS):
        for d in [D, -D]:
            x, y, z = custom_straight(d, vmax, a, kh, kw, ks)
            dr.append(x)
            wo.append(y)
            ti.append(z)
    stats("C-STR v%d a%d kh%d kw%s ks%d" % (vmax, a, kh, kw, ks), dr, wo, ti)


def custom_turn(ang, wmax, a, kt):
    sg = 1 if ang > 0 else -1
    dd = abs(ang)
    vp, ta, tc, T = prof(dd, wmax, a)
    h0 = hub.imu.heading()
    sw = StopWatch()
    t = 0
    while t < T * 1000 + 150:
        t = sw.time()
        sr, vr = ref(min(t / 1000, T), dd, vp, ta, tc, a, T)
        h = hub.imu.heading() - h0
        if abs(h) > dd + 60:
            lm.stop()
            rm.stop()
            print('ABORT turn', h)
            raise SystemExit
        c = (sg * vr + kt * (sg * sr - h)) * TW
        lm.run(c)
        rm.run(-c)
        wait(5)
    lm.hold()
    rm.hold()
    wait(250)
    return hub.imu.heading() - h0 - ang, int(T * 1000)


def custom_turn_set(wmax, a, kt):
    print('TW', TW)
    er = []
    ti = []
    for k in range(6):
        e, tt = custom_turn(90 if k % 2 == 0 else -90, wmax, a, kt)
        er.append(e)
        ti.append(tt)
    stats("C-TRN r%d a%d kt%d" % (wmax, a, kt), er, er, ti)


for cfg in [(500, 3000, 2), (500, 3000, 1)]:
    builtin_turn(cfg[0], cfg[1], cfg[2])

robot.stop()
wait(300)
TW = 2.6
for cfg in [(500, 3000, 8), (500, 3000, 12), (600, 3000, 8), (400, 2000, 8), (500, 2000, 6), (500, 4000, 10)]:
    custom_turn_set(cfg[0], cfg[1], cfg[2])
for tw in [2.5, 2.7]:
    TW = tw
    custom_turn_set(500, 3000, 8)
print("DONE")
