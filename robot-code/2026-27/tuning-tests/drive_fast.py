# drive_fast.py -- fast, straight, accurate driving for a 2-wheel SPIKE robot.
# Gyro heading hold + trapezoid motion profile. Tuned for 55 mm wheels,
# SPIKE Prime hub flat, large motors on A (left) and E (right).
# Run this file directly to execute the self-test (needs about 60 cm x 60 cm).
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.tools import wait, StopWatch
from umath import sqrt, pi


def _profile(dd, vmax, a):
    if dd >= vmax * vmax / a:
        vp = vmax
        ta = vp / a
        tc = (dd - vp * vp / a) / vp
    else:
        vp = sqrt(a * dd)
        ta = vp / a
        tc = 0
    return vp, ta, tc, 2 * ta + tc


def _ref(t, dd, vp, ta, tc, a, T):
    if t >= T:
        return dd, 0
    if t < ta:
        return 0.5 * a * t * t, a * t
    if t < ta + tc:
        return 0.5 * a * ta * ta + vp * (t - ta), vp
    td = T - t
    return dd - 0.5 * a * td * td, a * td


class FastDrive:
    def __init__(self, hub, left, right, wheel_mm=55, tw=2.5,
                 v=650, a=3000, kh=15, kw=0.1, ks=6,
                 turn_rate=500, turn_acc=3000, kt=8):
        # tw = wheel degrees per body degree when spinning in place (calibrated).
        # Keep a >= 3000 and turn_acc >= 3000: gentle accelerations were worse.
        self.hub = hub
        self.l = left
        self.r = right
        self.dpm = 360 / (pi * wheel_mm)
        self.tw = tw
        self.v = v
        self.a = a
        self.kh = kh
        self.kw = kw
        self.ks = ks
        self.turn_rate = turn_rate
        self.turn_acc = turn_acc
        self.kt = kt
        self.target = hub.imu.heading()

    def _abort(self, what, val):
        self.l.stop()
        self.r.stop()
        print("ABORT", what, val)
        raise SystemExit

    def error(self):
        return self.hub.imu.heading() - self.target

    def straight(self, mm, v=None, a=None):
        v = v or self.v
        a = a or self.a
        sg = 1 if mm > 0 else -1
        dd = abs(mm)
        vp, ta, tc, T = _profile(dd, v, a)
        self.l.reset_angle(0)
        self.r.reset_angle(0)
        hp = self.error()
        tp = 0
        w = 0
        sw = StopWatch()
        t = 0
        while t < T * 1000 + 200:
            t = sw.time()
            sr, vr = _ref(min(t / 1000, T), dd, vp, ta, tc, a, T)
            s = (self.l.angle() + self.r.angle()) / 2 / self.dpm
            h = self.error()
            if t > tp:
                w = 0.6 * w + 0.4 * (h - hp) * 1000 / (t - tp)
            hp = h
            tp = t
            if abs(h) > 40 or abs(s) > dd + 60:
                self._abort("straight", h)
            c = (-self.kh * h - self.kw * w) * self.tw
            base = (sg * vr + self.ks * (sg * sr - s)) * self.dpm
            self.l.run(base + c)
            self.r.run(base - c)
            wait(5)
        self.l.hold()
        self.r.hold()
        wait(150)

    def turn(self, deg, rate=None, acc=None):
        # Turns to an absolute heading (target += deg) so errors never accumulate.
        rate = rate or self.turn_rate
        acc = acc or self.turn_acc
        self.target += deg
        delta = self.target - self.hub.imu.heading()
        sg = 1 if delta > 0 else -1
        dd = abs(delta)
        if dd < 0.5:
            return
        vp, ta, tc, T = _profile(dd, rate, acc)
        h0 = self.hub.imu.heading()
        sw = StopWatch()
        t = 0
        while t < T * 1000 + 150:
            t = sw.time()
            sr, vr = _ref(min(t / 1000, T), dd, vp, ta, tc, acc, T)
            h = self.hub.imu.heading() - h0
            if abs(h) > dd + 60:
                self._abort("turn", h)
            c = (sg * vr + self.kt * (sg * sr - h)) * self.tw
            self.l.run(c)
            self.r.run(-c)
            wait(5)
        self.l.hold()
        self.r.hold()
        wait(150)


def _stats(name, errs):
    n = len(errs)
    print(name, "n", n, "mean|err|", round(sum([abs(e) for e in errs]) / n, 2),
          "max|err|", round(max([abs(e) for e in errs]), 2))


if __name__ == "__main__":
    hub = PrimeHub()
    left = Motor(Port.A, Direction.COUNTERCLOCKWISE)
    right = Motor(Port.E, Direction.CLOCKWISE)
    hub.imu.reset_heading(0)
    d = FastDrive(hub, left, right)
    SIDE = 120
    sw = StopWatch()

    errs = []
    for i in range(10):
        d.straight(SIDE)
        errs.append(d.error())
        d.straight(-SIDE)
        errs.append(d.error())
    _stats("TEST1 straight out/back heading", errs)

    errs = []
    for i in range(12):
        d.turn(90 if i % 2 == 0 else -90)
        errs.append(d.error())
    _stats("TEST2 turns 90 alternating", errs)

    errs = []
    for lap in range(5):
        for k in range(4):
            d.straight(SIDE)
            d.turn(90)
        errs.append(d.error())
    _stats("TEST3 square CW laps", errs)
    print("TEST3 final heading target", d.target, "gyro", round(hub.imu.heading(), 1))

    errs = []
    for lap in range(5):
        for k in range(4):
            d.straight(SIDE)
            d.turn(-90)
        errs.append(d.error())
    _stats("TEST4 square CCW laps", errs)
    print("TIME s", sw.time() // 1000)
    print("DONE")
