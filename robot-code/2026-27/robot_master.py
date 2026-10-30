# robot_master.py -- drive base + attachment arm control, all in one file.
# Hub: SPIKE Prime. Drive motors A (left) / E (right), 55 mm wheels. Arms on B (left) / F (right).
# Import from another file:   from robot_master import make_drive, make_arm
# Run this file directly:     it only prints "robot_master loaded" unless RUN is set below.
#
# FUNCTION INDEX (see the table in the hand-off notes for full usage)
#   make_drive(hub=None)                 -> FastDrive  (checks battery, waits for the robot to be still, zeroes gyro)
#   FastDrive.straight(mm, v, a)         drive straight with gyro heading hold
#   FastDrive.turn(deg, rate, acc)       turn to an ABSOLUTE heading (target += deg)
#   FastDrive.square_to_wall(backwards=True, heading=None)  back into a wall, reset gyro drift -> True/False
#   FastDrive.error()                    heading error in degrees (gyro - target)
#   check_battery(hub) / wait_until_still(hub)               start-up checks (make_drive calls both)
#   make_arm(name)                       -> Arm  (settings from ATTACHMENTS)
#   make_arms()                          -> {"left_arm": Arm, "right_arm": Arm}  (all attachments)
#   home_arms(arms)                      home every arm with home=True; zero the rest
#   Arm.home(...)                        slow stall-home toward the home stop
#   Arm.home_and_park(park_deg)          home, set zero, move off the stop
#   Arm.move_to(deg) / move_by(deg)      position moves in ARM degrees (clamped; times out if jammed, see Arm.ok)
#   Arm.set_gears([20, [12, 12], 12])    use a new gear train (before homing); gear_ratio(train) -> motor deg per arm deg
#   Arm.angle() / hold() / release() / load() / zero()
#   measure_travel(arm, direction, ...)  find an arm's range safely (slow, load-logged)
#   self_test_drive(d) / self_test_arm(arm) / hold_test(arm)   accuracy checks
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction, Stop, Color
from pybricks.tools import wait, StopWatch
from umath import sqrt, pi

# ============================ USER CONFIG ============================
RUN = None  # None | "drive" | "arm" | "all"  (what to run when this file is run directly)

# --- drive base (tuned on 55 mm grippy wheels) ---
WHEEL_MM = 55
TW = 2.5  # wheel degrees per body degree when spinning in place (calibrated; 2.73 from tape measure)
DRIVE_LEFT = (Port.A, Direction.COUNTERCLOCKWISE)
DRIVE_RIGHT = (Port.E, Direction.CLOCKWISE)
DRIVE_MOTOR_ACC = 20000  # deg/s^2 motor acceleration limit. The default (2000) kept the wheels from following the
#                          planned speed, so the robot overshot every distance. Set to None to restore the old behavior.
DRIVE_V = 480  # mm/s top speed. Motors top out near 1000 deg/s (about 540 mm/s), so the old 650 was unreachable
DRIVE_A = 3000  # mm/s^2 (the wheels can follow this only because of DRIVE_MOTOR_ACC)
DRIVE_KH = 15  # heading feedback gain
DRIVE_KW = 0.1  # heading-rate damping
DRIVE_KS = 6  # distance feedback gain
TURN_RATE = 300  # deg/s. Wheel speed = rate x TW must stay under ~1000 deg/s (500 overshot turns by 2-4 deg)
TURN_ACC = 3000  # deg/s^2
TURN_KT = 8

# --- start-up checks (make_drive) ---
STILL_MS = 300  # the hub must be still this long before the gyro is zeroed
STILL_MAX_MS = 3000  # give up waiting after this and zero anyway (prints a warning)
BATTERY_WARN_MV = 7500  # below this: warning + orange light. Full SPIKE battery ~8300 mV. Tuning was done on a charged one.

# --- wall squaring (FastDrive.square_to_wall) ---
SQUARE_SPEED = 120  # mm/s into the wall
SQUARE_TORQUE = 120  # mNm per wheel: enough to roll and seat both wheels, gentle on the models
SQUARE_MAX_MM = 300  # give up if no wall within this distance

# --- arm move timeout ---
ARM_TIMEOUT_EXTRA_MS = 800  # move_to waits the planned move time plus this, then gives up (arm jammed)

# --- data log ---
LOG = True  # True: print one "LOG," line after every drive / turn / square / arm move (see LOG NOTES at the bottom)
RUN_NAME = ""  # name shown on the dashboard for this run (robot.py start("Run 1") sets it)

# --- arm control (tuned on large motors) ---
ARM_KP_X = 4  # multipliers on the motor's built-in PID defaults
ARM_KI_X = 1
ARM_KD_X = 1
# (speed deg/s, acceleration deg/s^2) in MOTOR degrees
ARM_PROFILES = {
    "precise": (600, 3000),  # ~475 ms for 180 deg, no overshoot
    "fast": (1000, 8000),  # ~290 ms for 180 deg, <= 1 deg overshoot
}
# When a move counts as DONE (motor degrees, deg/s). The motor's default is loose: on 2026-10-27 every
# left arm 8 -> 90 move was logged +6.7..+11.7 arm deg past the target while the motor was still pulling back
# (negative load), i.e. "done" while still swinging - and the next command started then. October's settled
# readings were within 0.1 deg, so the arm does get there; these make move_to wait until it has.
ARM_TOL_POS = 2  # within 2 motor degrees of the target ...
ARM_TOL_SPEED = 20  # ... and moving slower than 20 deg/s

# One entry per attachment. Edit gears / sign / limits when the attachment changes.
#   gears    : the gear train the settings below were measured with, teeth in order from the MOTOR gear
#              to the ARM gear. Two gears on the same axle go in brackets: [20, [12, 12], 12].
#              None = no gears recorded (angles are then motor degrees). See gear_ratio().
#              A run can enter different gears (robot.py gears(), Arm.set_gears) without editing this.
#   sign     : +1/-1 so positive output degrees = the physical direction you want (with these gears)
#   home_dir : MOTOR direction (+1/-1) that runs toward the home stop (with these gears)
#   min_deg / max_deg : safe range in ARM (output) degrees
#   home     : True = stall-home against a hard stop at start (home_arms). False = just call
#              the current position zero (use when there is no hard stop or no attachment yet).
#   home_offset : the angle the home stop gets (default 0). Lets the arm's usual start position stay 0 when it
#              is homed: e.g. -72 = the stop is 72 deg below where the arm normally starts. arm_setup.py measures it.
#   home_torque : push used while homing, mNm (default 50). Raise it if homing "finds" a stop without moving.
#   home_ref : "relaxed" (default) = the stop is where the arm rests after homing lets go; "pushed" = where it was
#              while still pushing (use it when the stop was measured while pushing, as arm_setup.py measures it).
#   start_deg : where the arm goes after homing (default: just off the stop). 0 = back to its usual start position.
ATTACHMENTS = {
    # Left arm on port B: motor 20T -> 12T, that 12T shares an axle with a 12T -> 12T on the arm.
    # 0.6 motor deg per arm deg (arm turns 1.67x faster than the motor), 2 meshes = same direction as the motor.
    # Motor + = down onto the lowest stop, so sign=-1 makes UP positive. Range was measured as 5..400 MOTOR
    # degrees before the gears were entered = 8..667 arm degrees (the 400 / 667 top is still a placeholder).
    "left_arm": dict(port=Port.B, gears=[20, [12, 12], 12], sign=-1, home_dir=1, min_deg=8, max_deg=667,
                     profile="precise", home=True),
    # Right arm on port F: same gears as the left arm (20 > (12+12) > 12, 0.6 motor deg per arm deg), so angles are
    # ARM degrees. Measured with arm_setup.py on 2026-10-27, 3 runs from its usual start position (= 0), in motor deg:
    #   far stop -124 / -125 / -125 (at rest), near stop +23 / +23 / +24 (while pushing at 100 mNm).
    #   In arm degrees: far stop -208, near stop +39 (pushed).
    # It homes toward the NEAR stop (home_dir=+1; the far one was 125 motor deg away, the wrong way - fixed
    # 2026-10-28), counts that stop as +39 while pushing on it (home_ref="pushed", the same way it was measured), then
    # goes back to 0. home_torque=100: at 50 mNm the arm did not move at all, so homing would "find" a stop where it
    # sits. min_deg = 6 motor deg off the far stop; max_deg = 25 keeps it clear of the near stop (the arm springs back
    # ~9 motor deg after pushing). Run_A.py's right arm numbers were converted to arm degrees on 2026-10-28.
    "right_arm": dict(port=Port.F, gears=[20, [12, 12], 12], sign=1, home_dir=1, home_ref="pushed", home_offset=39,
                      home_torque=100, start_deg=0, min_deg=-198, max_deg=25, profile="precise", home=True),
}
LEGO_GEARS = (1, 8, 12, 14, 16, 20, 24, 28, 36, 40, 60)  # usual tooth counts (1 = worm gear); others get a warning
# =====================================================================


def _rnd(x, n):
    return round(x * 1.0, n)  # MicroPython can't round() an int with digits


# ============================ GEARS ============================
# A gear train is a list of teeth in order from the MOTOR gear to the ARM gear, e.g. [12, 36].
# Two gears on the same axle go in brackets together, the one being driven first: [20, [12, 12], 12]
# = motor 20T drives a 12T, a 12T on that same axle drives the 12T on the arm.

def _axles(train):
    # [(driven gear, driving gear) per axle]. A single gear on an axle is both.
    return [(a[0], a[1]) if isinstance(a, (list, tuple)) else (a, a) for a in train]


def gear_ratio(train):
    # MOTOR degrees per ARM degree. 3.0 = the motor turns 3 times per arm turn (slower, stronger);
    # 0.6 = the arm turns 1.67x faster than the motor.
    ax = _axles(train)
    r = 1.0
    for i in range(len(ax) - 1):
        r = r * ax[i + 1][0] / ax[i][1]
    return r


def gear_meshes(train):
    # Number of places where two gears touch. Each one reverses the direction (spur gears).
    return len(train) - 1


def gear_text(train):
    out = []
    for a in train:
        out.append("(" + str(a[0]) + "+" + str(a[1]) + ")" if isinstance(a, (list, tuple)) else str(a))
    return " > ".join(out)


def gear_problem(train):
    # Returns what is wrong with a gear list (a sentence), or None if it can be used.
    if not isinstance(train, (list, tuple)) or len(train) == 0:
        return "write the teeth in order from the motor, like [12, 36]"
    for a in train:
        pair = a if isinstance(a, (list, tuple)) else [a]
        if isinstance(a, (list, tuple)) and len(a) != 2:
            return "brackets are for TWO gears on the same axle, like [12, 12]"
        for t in pair:
            if not isinstance(t, int) or t < 1:
                return "every gear must be a whole number of teeth, got " + str(t)
    return None


# ============================ DATA LOG ============================
LOG_COLUMNS = ("LOG,step,cmd,plan,dist_mm,left_mm,right_mm,gyro_change,wheel_change,heading_err,heading,"
               "arm_angle,arm_load,ok,ms,time_s,speed_pct,arm_dir")
log_rows = []  # every logged move as a tuple (same order as LOG_COLUMNS, without "LOG")
_log_clock = StopWatch()


def log_move(cmd, plan, dist="", left="", right="", gyro="", wheel="", err="", heading="", arm="", load="", ok=1, ms=0,
             speed="", arm_dir=""):
    # Records one move and prints it as a CSV line starting with "LOG," (header printed before the first one,
    # after a "LOG_NAME," line with RUN_NAME). The computer-side collector turns these lines into a CSV file.
    if not LOG:
        return
    if not log_rows:
        _log_clock.reset()
        print("LOG_NAME," + RUN_NAME)
        print(LOG_COLUMNS)
    row = (len(log_rows) + 1, cmd, plan, dist, left, right, gyro, wheel, err, heading, arm, load, ok, ms,
           _rnd(_log_clock.time() / 1000, 2), speed, arm_dir)
    log_rows.append(row)
    print("LOG," + ",".join([str(f) for f in row]))


def log_summary(hub=None):
    # Prints the worst numbers of the run from log_rows. Call it at the end of a run (robot.finish() does).
    if not log_rows:
        return
    worst_dist = worst_head = worst_arm = 0
    where_dist = where_head = where_arm = "-"
    failed = []
    for r in log_rows:
        step, cmd, plan, dist, err, arm, ok = r[0], r[1], r[2], r[3], r[8], r[10], r[12]
        if cmd == "drive" and abs(dist - plan) > abs(worst_dist):
            worst_dist, where_dist = dist - plan, step
        if err != "" and cmd != "square" and abs(err) > abs(worst_head):
            worst_head, where_head = err, step
        if arm != "" and abs(arm - plan) > abs(worst_arm):
            worst_arm, where_arm = arm - plan, step
        if not ok:
            failed.append(step)
    print("SUMMARY moves", len(log_rows), "| time", log_rows[-1][14], "s")
    print("SUMMARY worst drive distance error", _rnd(worst_dist, 1), "mm at step", where_dist)
    print("SUMMARY worst heading error", worst_head, "deg at step", where_head)
    print("SUMMARY worst arm error", _rnd(worst_arm, 1), "deg at step", where_arm)
    print("SUMMARY failed steps (timeout / no wall)", failed if failed else "none")
    if hub:
        print("SUMMARY battery", hub.battery.voltage(), "mV")
    print("LOG_END")


def _profile(dd, vmax, a):
    # Trapezoid (or triangle) motion profile for a move of dd with max speed vmax, accel a.
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


# ============================ DRIVE BASE ============================
class FastDrive:
    def __init__(self, hub, left, right, wheel_mm=WHEEL_MM, tw=TW,
                 v=DRIVE_V, a=DRIVE_A, kh=DRIVE_KH, kw=DRIVE_KW, ks=DRIVE_KS,
                 turn_rate=TURN_RATE, turn_acc=TURN_ACC, kt=TURN_KT):
        self.hub = hub
        self.l = left
        self.r = right
        if DRIVE_MOTOR_ACC:
            left.control.limits(acceleration=DRIVE_MOTOR_ACC)
            right.control.limits(acceleration=DRIVE_MOTOR_ACC)
        self.dpm = 360 / (pi * wheel_mm)  # wheel degrees per mm
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
        # Heading error in degrees: gyro heading minus the heading we are trying to hold.
        return self.hub.imu.heading() - self.target

    def _start(self):
        # Snapshot before a move for _rec: (left wheel deg, right wheel deg, gyro heading, stopwatch).
        return self.l.angle(), self.r.angle(), self.hub.imu.heading(), StopWatch()

    def _rec(self, cmd, plan, snap, ok=1, speed=""):
        # Logs what one move really did, from the encoders and the gyro (see LOG NOTES at the bottom).
        l0, r0, h0, sw = snap
        dl = (self.l.angle() - l0) / self.dpm
        dr = (self.r.angle() - r0) / self.dpm
        h = self.hub.imu.heading()
        log_move(cmd, plan, dist=_rnd((dl + dr) / 2, 1), left=_rnd(dl, 1), right=_rnd(dr, 1),
                 gyro=_rnd(h - h0, 2), wheel=_rnd((dl - dr) / 2 * self.dpm / self.tw, 2),
                 err=_rnd(h - self.target, 2), heading=_rnd(h, 2), ok=ok, ms=sw.time(), speed=speed)

    def straight(self, mm, v=None, a=None):
        # Drive mm (negative = backwards) while holding self.target heading with the gyro.
        v = v or self.v
        a = a or self.a
        sg = 1 if mm > 0 else -1
        dd = abs(mm)
        vp, ta, tc, T = _profile(dd, v, a)
        snap = self._start()
        self.l.reset_angle(0)
        self.r.reset_angle(0)
        snap = (0, 0, snap[2], snap[3])
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
        self._rec("drive", mm, snap, speed=int(v * 100 / self.v + 0.5))

    def turn(self, deg, rate=None, acc=None):
        # Turns to an ABSOLUTE heading (target += deg), so errors never accumulate.
        # Positive = clockwise.
        rate = rate or self.turn_rate
        acc = acc or self.turn_acc
        snap = self._start()
        self.target += deg
        delta = self.target - self.hub.imu.heading()
        sg = 1 if delta > 0 else -1
        dd = abs(delta)
        if dd < 0.5:
            self._rec("turn", deg, snap, speed=int(rate * 100 / self.turn_rate + 0.5))
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
        self._rec("turn", deg, snap, speed=int(rate * 100 / self.turn_rate + 0.5))

    def square_to_wall(self, backwards=True, heading=None, speed=SQUARE_SPEED, torque=SQUARE_TORQUE,
                       max_mm=SQUARE_MAX_MM):
        # Drives slowly into a wall or the table border until BOTH wheels stall, so the robot sits flat
        # against it, then resets the gyro: the robot is now exactly at the heading it should have, which
        # clears the drift built up so far. Use it only where the wall is square to that heading.
        # heading=None keeps the current target (normal case); pass a number to set a new one (e.g. 90).
        # Returns True on success, False if there was no wall within max_mm (gyro left alone).
        if heading is not None:
            self.target = heading
        sg = -1 if backwards else 1
        snap = self._start()
        old_l = self.l.control.limits()
        old_r = self.r.control.limits()
        self.l.control.limits(torque=torque)
        self.r.control.limits(torque=torque)
        self.l.reset_angle(0)
        self.r.reset_angle(0)
        snap = (0, 0, snap[2], snap[3])
        self.l.run(sg * speed * self.dpm)
        self.r.run(sg * speed * self.dpm)
        found = False
        hits = 0
        sw = StopWatch()
        limit_ms = max_mm / speed * 2000 + 1500
        while True:
            t = sw.time()
            # Each wheel keeps pushing gently after it touches, until the other one is in too.
            if t > 300 and self.l.control.stalled() and self.r.control.stalled():
                hits += 1
            else:
                hits = 0
            if hits >= 15:
                found = True
                break
            s = (abs(self.l.angle()) + abs(self.r.angle())) / 2 / self.dpm
            if s > max_mm or t > limit_ms:
                break
            wait(10)
        self.l.stop()
        self.r.stop()
        self.l.control.limits(*old_l)
        self.r.control.limits(*old_r)
        if not found:
            self._rec("square", sg, snap, ok=0)
            print("SQUARE FAILED: no wall within", max_mm, "mm, gyro not reset")
            return False
        wait(100)
        # Logged BEFORE the gyro reset, so heading_err on this line = the drift the wall just removed.
        self._rec("square", sg, snap)
        self.hub.imu.reset_heading(self.target)
        return True


def check_battery(hub):
    # Prints the battery voltage. Below BATTERY_WARN_MV: warning, orange light, short beep. Returns mV.
    mv = hub.battery.voltage()
    if mv < BATTERY_WARN_MV:
        print("WARNING: battery low", mv, "mV - charge it, turns and distances will be off")
        hub.light.on(Color.ORANGE)
        hub.speaker.beep(500, 300)
    else:
        print("battery", mv, "mV")
    return mv


def wait_until_still(hub, still_ms=STILL_MS, max_ms=STILL_MAX_MS):
    # Waits until the hub has been still for still_ms (hands off the robot) so the gyro zero is clean.
    # Returns False if it was still moving after max_ms (the zero may be off by a degree or more).
    sw = StopWatch()
    still = StopWatch()
    while sw.time() < max_ms:
        if not hub.imu.stationary():
            still.reset()
        elif still.time() >= still_ms:
            return True
        wait(10)
    print("WARNING: robot was moving during the gyro zero - keep hands off at the start")
    return False


def make_drive(hub=None):
    # Builds the drive from the config above, checks the battery, waits for the robot to be still
    # and zeroes the heading. Returns (drive).
    hub = hub or PrimeHub()
    left = Motor(DRIVE_LEFT[0], DRIVE_LEFT[1])
    right = Motor(DRIVE_RIGHT[0], DRIVE_RIGHT[1])
    check_battery(hub)
    wait_until_still(hub)
    hub.imu.reset_heading(0)
    return FastDrive(hub, left, right)


# ============================== ARMS ==============================
class Arm:
    def __init__(self, motor, gear=1.0, sign=1, profile="precise", min_deg=None, max_deg=None, home_dir=1,
                 do_home=True, name="arm", gears=None, home_offset=0, home_torque=50, start_deg=None,
                 home_ref="relaxed"):
        self.m = motor
        self.home_ref = home_ref  # "relaxed": the stop = where the arm rests after homing; "pushed": while pushing
        self.home_offset = home_offset  # angle the home stop gets after homing
        self.home_torque = home_torque  # push used while homing (mNm)
        self.start_deg = start_deg  # where to go after homing (None = just off the stop)
        self.name = name  # shown in the data log as "arm:<name>"
        self.do_home = do_home
        self.gear = gear_ratio(gears) if gears else gear
        self.gears = gears
        self.sign = sign
        self.profile = profile
        self.min_deg = min_deg
        self.max_deg = max_deg
        self.home_dir = home_dir
        # The gears sign / home_dir were measured with. set_gears() compares new gears against these.
        self.ref_gears = gears
        self.ref_sign = sign
        self.ref_home_dir = home_dir
        self.ok = True  # False after a move_to that timed out
        self._pending = None  # (target, time limit ms, stopwatch) of a move not yet logged
        b = motor.control.pid()
        motor.control.pid(int(b[0] * ARM_KP_X), int(b[1] * ARM_KI_X), int(b[2] * ARM_KD_X), b[3], b[4])
        motor.control.target_tolerances(speed=ARM_TOL_SPEED, position=ARM_TOL_POS)
        self.zero()

    def set_gears(self, train):
        # Uses a new gear train (teeth from the MOTOR gear to the ARM gear, see GEARS). Call it BEFORE homing.
        # Angles, min_deg / max_deg stay in ARM degrees, so the same numbers mean the same arm positions.
        # If the number of meshes is odd where the measured gears had an even number (or the other way),
        # the arm turns the other way round: sign and home_dir are flipped to match.
        # Returns False and changes nothing if the list cannot be used.
        problem = gear_problem(train)
        if problem:
            print("GEARS", self.name, "NOT USED:", problem)
            return False
        self.gear = gear_ratio(train)
        self.gears = train
        flipped = False
        if self.ref_gears:
            flipped = gear_meshes(train) % 2 != gear_meshes(self.ref_gears) % 2
            self.sign = -self.ref_sign if flipped else self.ref_sign
            self.home_dir = -self.ref_home_dir if flipped else self.ref_home_dir
        r = self.gear
        how = "arm turns " + str(_rnd(1 / r, 2)) + "x faster than the motor" if r < 1 else \
            "motor turns " + str(_rnd(r, 2)) + "x per arm turn (slower, stronger)" if r > 1 else "same speed as the motor"
        print("GEARS", self.name, gear_text(train), "|", how)
        if flipped:
            print("GEARS", self.name, "turns the other way with these gears: direction flipped to match")
        if not self.ref_gears:
            print("GEARS", self.name, "no measured gears to compare with: check which way is up by hand first")
        odd = []
        for a in train:
            for t in (a if isinstance(a, (list, tuple)) else [a]):
                if t not in LEGO_GEARS and t not in odd:
                    odd.append(t)
        if odd:
            print("GEARS", self.name, "unusual tooth count", odd, "- check you counted right")
        if 1 in [a[1] for a in _axles(train)]:
            print("GEARS", self.name, "worm gear: direction depends on how it is built, check it by hand")
        log_move("gears:" + self.name, _rnd(self.gear, 3))
        return True

    def zero(self):
        # Call only when the attachment is physically at its zero position.
        self.m.reset_angle(0)

    def angle(self):
        # Output degrees (positive = the direction chosen by sign).
        return self.m.angle() / self.gear * self.sign

    def error_to(self, out_deg):
        return self.angle() - out_deg

    def move_to(self, out_deg, profile=None, wait_done=True, speed_pct=100):
        # Moves to an output angle (clamped to min_deg/max_deg). Holds position at the end.
        # speed_pct scales the profile speed (100 = normal). wait_done=False starts the move and returns at
        # once (drive or move the other arm meanwhile); call wait_done() later to finish and log it.
        # It gives up after the planned move time + ARM_TIMEOUT_EXTRA_MS (arm jammed on a model): it holds
        # where it is, prints a warning and the run carries on. self.ok says which.
        if self._pending:
            self._finish_pending(interrupted=True)
        if self.min_deg is not None and out_deg < self.min_deg:
            out_deg = self.min_deg
        if self.max_deg is not None and out_deg > self.max_deg:
            out_deg = self.max_deg
        sp, ac = ARM_PROFILES[profile or self.profile]
        sp = sp * speed_pct / 100
        self.m.control.limits(speed=sp, acceleration=ac)
        target = out_deg * self.gear * self.sign
        travel = abs(target - self.m.angle())
        direction = "up" if out_deg >= self.angle() else "down"
        self.m.run_target(sp, target, then=Stop.HOLD, wait=False)
        self.ok = True
        self._pending = (out_deg, (travel / sp + sp / ac) * 1000 + ARM_TIMEOUT_EXTRA_MS, StopWatch(),
                         int(speed_pct + 0.5), direction)
        if wait_done:
            self.wait_done()
        return out_deg

    def wait_done(self):
        # Waits for the last move_to to finish (or time out) and logs it. Returns self.ok. Safe to call
        # when nothing is moving.
        if self._pending:
            out_deg, limit_ms, sw = self._pending[:3]
            while not self.m.control.done():
                if sw.time() > limit_ms:
                    self.m.hold()  # stop pushing: hold the spot it reached
                    self.ok = False
                    print("ARM TIMEOUT:", self.name, "wanted", out_deg, "got", _rnd(self.angle(), 1),
                          "after", sw.time(), "ms")
                    break
                wait(5)
            self._finish_pending()
        return self.ok

    def _finish_pending(self, interrupted=False):
        # Logs the last move. interrupted = a new move_to replaced it before it finished (ok=0 if it was
        # more than 2 deg short).
        out_deg, limit_ms, sw, pct, direction = self._pending
        self._pending = None
        if interrupted and abs(self.angle() - out_deg) > 2:
            self.ok = False
        log_move("arm:" + self.name, _rnd(out_deg, 1), arm=_rnd(self.angle(), 1), load=self.load(),
                 ok=1 if self.ok else 0, ms=sw.time(), speed=pct, arm_dir=direction)

    def move_by(self, delta, profile=None, wait_done=True):
        return self.move_to(self.angle() + delta, profile, wait_done)

    def hold(self):
        self.m.hold()

    def release(self):
        self.m.stop()

    def load(self):
        # Estimated torque on the motor in mNm.
        return self.m.load()

    def home(self, direction=None, speed=60, torque=50, max_travel=400, reset=True):
        # Slowly drive toward a hard stop (60 deg/s, 50 mNm cap) until the motor stalls.
        # direction = MOTOR direction (+1/-1); default = self.home_dir.
        # Returns (found, travel_in_motor_degrees). On success and reset=True, that point is zero.
        # Gives up (found=False) after max_travel motor degrees or a time limit.
        if direction is None:
            direction = self.home_dir
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
            t = sw.time()
            if not moving and abs(m.speed()) > 0.7 * speed:
                moving = True
            # Count a stall only after the motor reached speed, or after 0.8 s if it never
            # moved (already resting on the stop). Require ~150 ms of persistence.
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
        pushed = m.angle()  # where the motor was while still pushing on the stop
        travel = pushed - start
        m.stop()
        wait(200)
        if found and reset:
            if self.home_ref == "pushed":
                m.reset_angle(m.angle() - pushed)  # 0 = the pushed position; the arm sits where it sprang back to
            else:
                m.reset_angle(0)  # 0 = where it rests after letting go
        sp, ac = ARM_PROFILES[self.profile]
        m.control.limits(speed=sp, acceleration=ac, torque=199)
        return found, travel

    def home_and_park(self, park_deg=5, max_travel=400):
        # Full homing: find the stop, call it home_offset (0 unless set), then move park_deg away so the
        # controller is not pushing on the stop. Returns True on success.
        # If no stop is found it releases the motor and returns False. Check the result!
        found, travel = self.home(torque=self.home_torque, max_travel=max_travel)
        if not found:
            self.release()
            print("HOME FAILED: no stop within", max_travel, "motor deg (travel", int(travel), ")")
            return False
        if abs(travel) < 3 and self.home_offset:
            print("HOME NOTE:", self.name, "found its stop without moving. Fine if it started resting on the stop;",
                  "if not, stop the program - it would now count from the wrong place.")
        if self.home_offset:
            self.m.reset_angle(self.m.angle() + self.home_offset * self.gear * self.sign)
        if self.start_deg is not None:
            self.move_to(self.start_deg)  # back to the usual start position
        else:
            away = -self.home_dir * self.sign  # arm-degree direction away from the stop
            self.move_to(self.home_offset + away * park_deg)
        return True


def make_arm(name):
    # Builds an Arm from ATTACHMENTS[name]. Does NOT move it; call home_and_park() to home.
    c = ATTACHMENTS[name]
    return Arm(Motor(c["port"]), gear=c.get("gear", 1.0), sign=c["sign"], profile=c["profile"],
               min_deg=c["min_deg"], max_deg=c["max_deg"], home_dir=c["home_dir"],
               do_home=c.get("home", True), name=name, gears=c.get("gears"), home_offset=c.get("home_offset", 0),
               home_torque=c.get("home_torque", 50), start_deg=c.get("start_deg"), home_ref=c.get("home_ref", "relaxed"))


def make_arms():
    # Builds EVERY arm in ATTACHMENTS. Returns a dict: {"left_arm": Arm, "right_arm": Arm}. Does not move anything.
    arms = {}
    for name in ATTACHMENTS:
        arms[name] = make_arm(name)
    return arms


def home_arms(arms, park_deg=5):
    # Homes every arm that has home=True (stall-home, zero, park). Arms with home=False are simply
    # zeroed where they sit. Returns True only if every stall-home succeeded.
    ok = True
    for name in arms:
        a = arms[name]
        if a.do_home:
            if not a.home_and_park(park_deg):
                print("home_arms: FAILED for", name)
                ok = False
        else:
            a.zero()
            print("home_arms:", name, "not stall-homed, zeroed in place")
    return ok


def measure_travel(arm, direction, max_travel=720, speed=60, torque=80, mark=30):
    # Slowly drives the arm AWAY from its home stop (direction = MOTOR direction, normally
    # -arm.home_dir) and logs speed and load every "mark" motor degrees. Stops at a stall or
    # max_travel. Returns (found_stop, travel_motor_deg, marks). Afterwards call
    # arm.home_and_park() to bring it back. Use only where the arm cannot hit anything.
    m = arm.m
    m.control.limits(speed=speed, torque=torque)
    start = m.angle()
    m.run(speed * direction)
    moving = False
    hits = 0
    found = False
    marks = []
    nxt = mark
    sw = StopWatch()
    limit_ms = max_travel / speed * 2000 + 1500
    while True:
        t = sw.time()
        d = abs(m.angle() - start)
        if not moving and abs(m.speed()) > 0.7 * speed:
            moving = True
        if m.control.stalled() and (moving or t > 800):
            hits += 1
        else:
            hits = 0
        if d >= nxt:
            marks.append((int(d), int(m.speed()), int(m.load())))
            nxt += mark
        if hits >= 15:
            found = True
            break
        if d > max_travel or t > limit_ms:
            break
        wait(10)
    travel = abs(m.angle() - start)
    m.stop()
    sp, ac = ARM_PROFILES[arm.profile]
    m.control.limits(speed=sp, acceleration=ac, torque=199)
    return found, travel, marks


# ============================ SELF-TESTS ============================
def _stats(name, errs):
    n = len(errs)
    print(name, "n", n, "mean|err|", _rnd(sum([abs(e) for e in errs]) / n, 2),
          "max|err|", _rnd(max([abs(e) for e in errs]), 2))


def self_test_drive(d, side=120):
    # Needs about 60 cm x 60 cm of floor. ~80 s. Prints heading errors in degrees.
    errs = []
    for i in range(10):
        d.straight(side)
        errs.append(d.error())
        d.straight(-side)
        errs.append(d.error())
    _stats("DRIVE straight out/back", errs)
    errs = []
    for i in range(12):
        d.turn(90 if i % 2 == 0 else -90)
        errs.append(d.error())
    _stats("DRIVE turns 90 alternating", errs)
    errs = []
    for lap in range(5):
        for k in range(4):
            d.straight(side)
            d.turn(90)
        errs.append(d.error())
    _stats("DRIVE square CW laps", errs)
    print("DRIVE final heading target", d.target, "gyro", _rnd(d.hub.imu.heading(), 1))


def self_test_arm(name, arm, targets, win=1500):
    # Moves through targets (output degrees) twice and reports final error / overshoot / jitter.
    errs = []
    overs = []
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
    print(name, "n", len(errs), "|final err mean", _rnd(sum(errs) / len(errs), 2), "max", _rnd(max(errs), 2),
          "|overshoot max", _rnd(max(overs), 2), "|jitter max", _rnd(max(jit), 2))


def hold_test(name, arm, target, seconds=3):
    # Holds a position and reports drift and the peak load (mNm). Add weight to the arm to test real loads.
    arm.move_to(target)
    wait(300)
    lo = 99999
    hi = -99999
    ld = 0
    sw = StopWatch()
    while sw.time() < seconds * 1000:
        a = arm.angle()
        lo = min(lo, a)
        hi = max(hi, a)
        l = abs(arm.load())
        if l > ld:
            ld = l
        wait(10)
    print(name, "HOLD", seconds, "s at", target, "| drift range", _rnd(hi - lo, 2), "deg | peak load", _rnd(ld, 1), "mNm")


if __name__ == "__main__":
    print("robot_master loaded")
    if RUN in ("drive", "all"):
        drv = make_drive()
        self_test_drive(drv)
    if RUN in ("arm", "all"):
        left_arm = make_arm("left_arm")
        if left_arm.home_and_park():
            top = left_arm.max_deg
            self_test_arm("left_arm precise", left_arm, [8, top, top / 2, top / 4, top * 3 / 4, 8])
            left_arm.profile = "fast"
            self_test_arm("left_arm fast", left_arm, [8, top, top / 2, top / 4, top * 3 / 4, 8])
            left_arm.profile = "precise"
            hold_test("left_arm", left_arm, top / 2)
            left_arm.move_to(8)
            left_arm.release()
    if RUN:
        print("DONE")


# ======================================================================================
# ARM TUNING AND TESTING GUIDE  (comments only, safe to leave in the file)
# ======================================================================================
#
# 1. WHAT IS TUNED NOW
#    PID: kp x4, ki x1, kd x1 on the motor's built-in defaults (ARM_KP_X / ARM_KI_X / ARM_KD_X).
#    The defaults were too soft: a 180 deg move still sat 1.7-3 deg off after 1 s and took 800-1000 ms.
#    Profiles (motor degrees): "precise" 600 deg/s, 3000 deg/s^2  -> ~475 ms per 180 deg, no overshoot
#                              "fast"    1000 deg/s, 8000 deg/s^2 -> ~290 ms per 180 deg, <= 1 deg overshoot
#    15000 deg/s^2 gave an occasional outlier on the left arm (then on port C): do not go that high.
#    All of this was tuned on BARE large motors and then checked on the left arm (on port C at the time, now B). The right arm (F) has
#    no attachment yet, so nothing here has been verified for it under load.
#    UNITS: everything in sections 2-7 was measured before the gears were entered (gear 1.0), so arm angles
#    there are MOTOR degrees. With the left arm's 20 > (12+12) > 12 gears, arm degrees = motor degrees x 1.67.
#
# 2. RESULTS TO COMPARE AGAINST (left arm, then on port C, 12 moves between 5 and 400 deg, gear 1.0)
#      profile   final error mean / max   overshoot max   jitter at rest
#      precise   0.08 deg / 1.0 deg       5 deg           0 deg
#      fast      0.42 deg / 1.0 deg       4 deg           0 deg
#    The overshoot is the arm settling onto its lowest stop when the target is 5 deg, so it is capped
#    by that margin. Hold test: 200 deg for 3 s -> 0.0 deg drift, peak load 15 mNm (arm weight only).
#    Lifting at 60 deg/s needed only 0-25 mNm, but the speed was uneven (40-111 deg/s): the mechanism
#    has some stick-slip. Angles read in whole degrees, so errors under 1 deg are not meaningful.
#
# 3. ADDING OR CHANGING AN ATTACHMENT (do these in order)
#    a. Make sure a motor is plugged into the port, then add an entry to ATTACHMENTS with home=False,
#       gear=1.0, sign=1, min_deg=None, max_deg=None.
#    b. Direction: a = make_arm("name"); a.release(); turn it by hand and print a.angle(). Then
#       a.move_by(20) with your hand near it. If it goes the wrong way, set sign=-1.
#    c. Gear ratio: set a known output angle by hand (for example 90 deg), print a.m.angle().
#       gear = motor degrees / output degrees. Put it in ATTACHMENTS.
#    d. Home stop: only if there is a hard stop that is safe to touch at 60 deg/s and 50 mNm.
#       found, travel = a.home(); print(found, travel). Expect found=True. Then set home=True and
#       home_dir to the MOTOR direction that reaches that stop (+1 or -1).
#    e. Range: with the arm clear of everything, found, t, marks = measure_travel(a, -a.home_dir).
#       Then a.home_and_park(). Set max_deg to (t / gear) minus a margin of 5-10 deg, min_deg to 5.
#       If found is False the arm kept moving to the cap, so there is no stop on that side. Set the
#       limit yourself from a physical measurement.
#    f. Accuracy: self_test_arm("name", a, [5, top, top/2, top/4, top*3/4, 5]).
#    g. Load: hold_test("name", a, top/2) with the real load hanging on it.
#
# 4. TUNING RULES (change one thing at a time, re-run the same tests)
#      symptom                                   try
#      sags or ends short under load             raise ARM_KI_X to 2, then 3. Re-check overshoot.
#      vibrates, buzzes, jitter at rest          lower ARM_KP_X to 3, or raise ARM_KD_X to 1.2.
#      overshoots the target                     use "precise", or raise ARM_KD_X a little.
#      too slow                                  use "fast", but only after checking overshoot WITH load.
#      misses by a fixed amount in one direction approach the target from the same side every time.
#      cannot lift the load at all               check the load reading; the motor torque cap is 199 mNm.
#    What not to do: kp x6 or x8 with kd unchanged overshot up to 8 deg and jittered up to 14 deg;
#    kd x2 to x3 made settling slower. Keep kp and kd roughly in proportion.
#
# 5. TEST CHECKLIST (record the numbers each time)
#    [ ] self_test_arm: final error mean <= 1 deg, max <= 2 deg, jitter <= 1 deg.
#    [ ] hold_test with the real load: drift <= 1 deg over 3 s, load well below 199 mNm.
#    [ ] home_and_park from three starts: on the stop, halfway, near the top. Success every time.
#    [ ] Repeat the whole set at low battery and after a few minutes of running (motor warms up).
#    [ ] Run the arm through the full mission once, slowly, with your hand near the stop button.
#
# 6. HOMING NOTES AND SAFETY
#    - Always home toward the stop you have proven. Never stall-search toward an unknown end.
#    - home() uses 60 deg/s and 50 mNm. It counts a stall only after the motor reached speed, or after
#      0.8 s if it was already resting on the stop, and needs ~150 ms of persistence. It gives up after
#      max_travel motor degrees or a time limit and returns found=False. Always check the return value.
#    - Earlier versions raised false stalls while the motor was breaking away from rest, and hung when
#      the arm already sat on the stop. Both are fixed; if homing ever misbehaves, test with the
#      diagnostic idea: m.run(60) for 2 s and print m.angle(), m.speed(), m.load() every 200 ms.
#    - The left arm's (then port C) positive direction showed a stiff spot that stops a 50 mNm push but not a 100 mNm one.
#      That is the lowest stop of the left arm; do not raise the homing torque to push through it.
#    - Press the hub's center button to stop a program. Keep hands and cables clear of moving arms.
#
# 7. KNOWN LIMITS (not yet verified)
#    - The left arm's top stop was not found within 721 motor degrees, so max_deg=400 is a placeholder.
#    - Gear ratio of the left arm is unknown (gear=1.0 means output degrees equal motor degrees).
#    - Holding strength with a real game piece is untested. The right arm (F) is untested with an attachment.
#    - Importing this file from other programs works (see run_template2.py), but each import loads the
#      whole file, so edit the config once here, not in the mission files.
# ======================================================================================

# ======================================================================================
# DRIVE NOTES (found while debugging mission 4/5 on the real FLL map, October 2026)
#  - Motor.run(speed) is limited by the motor's acceleration limit (default 2000 deg/s^2, about 960 mm/s^2
#    on 55 mm wheels). FastDrive plans 3000 mm/s^2, so with the default limit the wheels could not speed up
#    or brake as planned: the robot overshot every move by 19-50 mm and swerved up to 20 deg at speed.
#    DRIVE_MOTOR_ACC raises the limit. The earlier acceleration tests only measured heading, never distance,
#    so they did not catch this.
#  - With DRIVE_MOTOR_ACC=20000, DRIVE_V=480, TURN_RATE=300 two runs of the same mission ended within
#    2.5 mm of each other and within about 4 mm of the ideal path; every straight was within 2 mm of plan.
#  - Distances in mission files are now the REAL distances. Numbers you inflated or shrank to compensate
#    for the old overshoot (650, 250, ...) must be changed back to the distances you actually want.
#  - Remaining known issues: a -62 deg turn still ended about 1.9 deg over; the left arm lands 4-6 deg off its
#    target on some moves (it overshoots 90 and 35 by a few degrees).
# ======================================================================================

# ======================================================================================
# ADDED 2026-10-27 (NOT YET TESTED ON THE ROBOT) -- check each one before a mission relies on it
#  - make_drive: prints the battery (warns + orange light + beep under BATTERY_WARN_MV) and waits up to
#    3 s for the hub to be still before zeroing the gyro. Test: start a run while holding the robot,
#    expect the "robot was moving" warning; hands off, expect none and no extra delay.
#  - Arm.move_to timeout: block the left arm with your hand during a move. Expect "ARM TIMEOUT", the arm
#    stops pushing, the run carries on, arm.ok is False. Normal moves must never time out: if one does,
#    raise ARM_TIMEOUT_EXTRA_MS.
#  - square_to_wall: place the robot ~10 cm from the border, a few degrees crooked. Call
#    d.square_to_wall() and check that both wheels touch, it returns True, and d.error() is about 0 after.
#    If it slides or stops before seating both wheels, raise SQUARE_TORQUE in steps of 20; if it bumps
#    hard, lower SQUARE_SPEED. Then: square, d.straight(300), and compare the heading error with and without.
#    Example in a mission:   drive.turn(-90); drive.square_to_wall(); drive.straight(400)
# ======================================================================================

# ======================================================================================
# LOG NOTES (added 2026-10-27)
#  Every drive / turn / square / arm move prints one line starting with "LOG," -- from robot.py, the
#  run templates, the debug file, anything that uses this file. LOG = False at the top turns it off.
#  The hub cannot save files, so the data lives in the Pybricks output window: after a run, select the
#  output, copy it, paste it into a spreadsheet (Data > Split text to columns, separator comma) and
#  keep only the lines that start with LOG. log_summary() prints the worst numbers at the end.
#  If the hub is not connected to the computer, the lines are simply lost; the run itself is not affected.
#
#  Columns:
#    step          1, 2, 3 ... in the order the moves ran
#    cmd           drive | turn | square | arm:<name>   (homing moves show up as arm moves too)
#                  gears:<name> = gears entered for that arm; plan = motor degrees per arm degree
#    plan          what was asked: mm for drive, degrees for turn, target angle for arms, -1/1 = back/forward for square
#    dist_mm       distance driven, average of both wheel encoders (compare with plan for drive)
#    left_mm / right_mm   each wheel on its own -- a big difference on a drive = slipping or bumping
#    gyro_change   how much the heading changed during the move, from the gyro
#    wheel_change  the same, worked out from the wheels (uses TW). gyro and wheel disagreeing = wheel slip
#    heading_err   gyro minus the heading the robot should have, at the end of the move (0 = perfect).
#                  On a square line this is the drift the wall just removed (the gyro is reset after it).
#    heading       absolute gyro heading at the end of the move (0 = start direction)
#    arm_angle     where the arm ended (compare with plan)
#    arm_load      motor load in mNm at the end of the arm move (high = pushing on something)
#    ok            1 = fine, 0 = arm timed out or square found no wall
#    ms            how long the move took
#    time_s        seconds since the first logged move
#    speed_pct     speed used, percent of normal (drive / turn / arm)
#    arm_dir       up | down for arm moves
#  Also: "LOG_NAME,<name>" just before the header (the run name) and "LOG_END" after the summary.
#  AUTOMATIC CSV FILES: robot-data\collect_runs.py (started by VS Code) saves every run to robot-data\runs\
#  and rebuilds robot-data\dashboard.html. See robot-data\README.txt.
# ======================================================================================
