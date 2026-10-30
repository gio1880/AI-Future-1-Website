# arm_drive.py -- tuned position control for attachment arms on ports C and D.
# Tuned with NO attachment mounted (bare large motors). Re-check holding strength
# once a real attachment is on: see the load notes at the bottom of this file.
# Run this file directly to execute the self-test (arms move up to 180 degrees).
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Stop
from pybricks.tools import wait, StopWatch

# PID multipliers on the motor's built-in defaults (kp x4, ki x1, kd x1).
KP_X = 4
KI_X = 1
KD_X = 1

# (speed deg/s, acceleration deg/s^2) in MOTOR degrees.
# precise: ~475 ms for a 180 degree move, no overshoot. fast: ~290 ms, <=1 degree overshoot.
PROFILES = {
    "precise": (600, 3000),
    "fast": (1000, 8000),
}


def _rnd(x, n):
    return round(x * 1.0, n)


class Arm:
    def __init__(self, motor, gear=1.0, sign=1, profile="precise", min_deg=None, max_deg=None):
        # gear: motor degrees per OUTPUT degree (same convention as arm_pid.py: 0.6 means
        #       the motor turns 0.6 degrees for each degree the attachment turns).
        # sign: +1 or -1 so that positive output degrees are the physical positive direction.
        # min_deg / max_deg: safe range in OUTPUT degrees (None = no limit).
        self.m = motor
        self.gear = gear
        self.sign = sign
        self.profile = profile
        self.min_deg = min_deg
        self.max_deg = max_deg
        b = motor.control.pid()
        motor.control.pid(int(b[0] * KP_X), int(b[1] * KI_X), int(b[2] * KD_X), b[3], b[4])
        self.zero()

    def zero(self):
        # Call only after the attachment is physically at its agreed zero position.
        self.m.reset_angle(0)

    def angle(self):
        return self.m.angle() / self.gear * self.sign

    def error_to(self, out_deg):
        return self.angle() - out_deg

    def move_to(self, out_deg, profile=None, wait_done=True):
        if self.min_deg is not None and out_deg < self.min_deg:
            out_deg = self.min_deg
        if self.max_deg is not None and out_deg > self.max_deg:
            out_deg = self.max_deg
        sp, ac = PROFILES[profile or self.profile]
        self.m.control.limits(speed=sp, acceleration=ac)
        target = out_deg * self.gear * self.sign
        self.m.run_target(sp, target, then=Stop.HOLD, wait=wait_done)
        return out_deg

    def move_by(self, delta, profile=None, wait_done=True):
        return self.move_to(self.angle() + delta, profile, wait_done)

    def home(self, direction=1, speed=60, torque=50, max_travel=360, reset=True):
        # Drive slowly in 'direction' (+1/-1, in MOTOR direction) until the motor stalls
        # against a hard stop, then call that point zero. Low torque protects the mechanism.
        # Gives up (and returns False) if no stall is found within max_travel motor degrees.
        m = self.m
        m.control.limits(speed=speed, torque=torque)
        start = m.angle()
        m.run(speed * direction)
        found = False
        moving = False
        hits = 0
        sw = StopWatch()
        limit_ms = max_travel / speed * 2000 + 1500
        while True:
            # Only count a stall after the motor has actually reached speed, and require
            # it to persist (avoids false alarms while breaking away from rest).
            if not moving and abs(m.speed()) > 0.7 * speed:
                moving = True
            t = sw.time()
            at_stop = m.control.stalled() and (moving or t > 800)
            if at_stop:
                hits += 1
            else:
                hits = 0
            if hits >= 15:
                found = True
                break
            if abs(m.angle() - start) > max_travel or t > limit_ms:
                break
            wait(10)
        travel = m.angle() - start
        m.stop()
        wait(200)
        if found and reset:
            m.reset_angle(0)
        sp, ac = PROFILES[self.profile]
        m.control.limits(speed=sp, acceleration=ac, torque=199)
        return found, travel

    def hold(self):
        self.m.hold()

    def release(self):
        self.m.stop()

    def load(self):
        # Estimated torque on the motor in mNm. Watch this to see how hard it works to hold.
        return self.m.load()


def _self_test(name, arm, targets=None, win=900):
    if targets is None:
        targets = [0, 90, -45, 180, 0, 135, -90, 45, 0, 180, -180, 0]
    errs = []
    overs = []
    times = []
    jit = []
    for t in targets * 2:
        start = arm.angle()
        sw = StopWatch()
        arm.move_to(t, wait_done=False)
        over = 0
        lo = 99999
        hi = -99999
        while sw.time() < win:
            e = (arm.angle() - t) * (1 if t >= start else -1)
            if e > over:
                over = e
            if sw.time() > win - 300:
                a = arm.angle()
                lo = min(lo, a)
                hi = max(hi, a)
            wait(4)
        errs.append(abs(arm.angle() - t))
        overs.append(over)
        jit.append(hi - lo)
    # Return to zero repeatedly: any drift shows up as a non-zero final angle.
    print(name, "n", len(errs),
          "|final err mean", _rnd(sum(errs) / len(errs), 2), "max", _rnd(max(errs), 2),
          "|overshoot max", _rnd(max(overs), 2),
          "|jitter max", _rnd(max(jit), 2),
          "|zero drift", _rnd(arm.angle(), 2))


def _hold_test(name, arm, t=90, back=0):
    arm.move_to(t)
    wait(300)
    lo = 99999
    hi = -99999
    ld = 0
    sw = StopWatch()
    while sw.time() < 3000:
        a = arm.angle()
        lo = min(lo, a)
        hi = max(hi, a)
        l = abs(arm.load())
        if l > ld:
            ld = l
        wait(10)
    print(name, "HOLD 3 s at", t, ": range", _rnd(hi - lo, 2), "deg | peak load mNm", _rnd(ld, 1))
    arm.move_to(back)


if __name__ == "__main__":
    hub = PrimeHub()
    m = Motor(Port.C)
    # Lift arm: motor + = down, motor - = up. sign=-1 so UP is positive. gear=1 -> output = motor degrees.
    a = Arm(m, gear=1.0, sign=-1, profile="precise", min_deg=5, max_deg=400)
    f, t = a.home(direction=1, speed=60, torque=50, max_travel=400)
    print("C DOWN stop found", f, "travel", t)
    if f:
        tg = [5, 400, 200, 100, 300, 5]
        for prof in ["precise", "fast"]:
            a.profile = prof
            _self_test("C " + prof, a, tg, 1500)
        a.profile = "precise"
        _hold_test("C", a, 200, 5)
        a.release()
    print("DONE")

# LOAD NOTES (do this when an attachment is mounted):
# 1. Set gear (motor deg per output deg), sign, and min_deg/max_deg for that attachment.
# 2. Start with profile "precise". Hold the arm at a target and print arm.load().
# 3. If the arm sags or creeps under load, raise KI_X to 2 (it removes steady error).
#    If it vibrates, lower KP_X to 3. Re-run the self-test after every change.
