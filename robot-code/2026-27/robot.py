# robot.py -- EASY commands for AI Future 1 students. All the hard work is in robot_master.py.
# Put this file, robot_master.py and your run file in the same Pybricks project.
# Settings (speeds, ports, arm limits) are changed in robot_master.py, never here.
#
# In your run file:
#     from robot import *
#     gears(left=[20, [12, 12], 12])
#     left_arm.homing(True)
#     right_arm.homing(False)
#     start("Run 1")
#     drive(300)
#     turn(90)
#     left_arm(90)
#     drive(-300)
#     finish()
#
# CHEAT SHEET     + = forward / right      - = backward / left
#   --- SETUP: these lines go BEFORE start() ---
#   gears(left=[...], right=[...])   the gears on each arm, teeth in order from the MOTOR to the ARM
#                               [12, 36] = motor 12T drives 36T.  [20, [12, 12], 12] = brackets = same axle.
#                               Leave an arm out to use the gears written in robot_master.py.
#   left_arm.homing(True)       at start, lower the arm gently onto its bottom stop and call that 0
#   left_arm.homing(False)      no homing (nothing mounted, or no stop): it counts where it is as 0,
#                               so put it in its start position by hand.   Same for right_arm.homing(...)
#                               (True and False start with a capital letter)
#   robot_homing(True)          at start, back gently into the wall behind the robot to line it up
#                               (it backs up to 10 cm until it touches - plan your run from touching the wall)
#   start("Run 1")              get ready: hands off! checks battery, zeroes the gyro, homes what you asked for.
#                               The name is what the dashboard shows - keep the same name for the same run.
#
#   --- DRIVING ---
#   drive(mm)                   + forward, - backward (10 mm = 1 cm), the gyro keeps it straight
#   turn(deg)                   + right (clockwise), - left
#   forward(mm)   back(mm)      same as drive, if you prefer words
#   turn_right(deg)  turn_left(deg)   same as turn, if you prefer words
#   face(deg)                   turn to face a direction: 0 = where it started, 90 = right, -90 = left, 180 = back
#   SPEED is a percent: 100 = normal (full), 50 = half, 25 = slow and careful. Lowest 10, highest 100.
#   drive(300, 50)              this one move at 50%  (works the same for turn, face, forward, back...)
#   set_speed(50)               every DRIVE and TURN after this at 50% ...
#   set_speed(100)              ... until you set it back (arms are not affected, give them their own speed)
#   square()                    back gently into the wall to straighten up (fixes gyro drift)
#
#   --- ARMS -- two of them, same commands:   left_arm = port B      right_arm = port F ---
#   left_arm(90)                go TO an angle of the ARM (gears are worked out for you): 8 = bottom, bigger = higher
#   left_arm.by(20)             move BY an amount from where it is: + up, - down (left_arm.by(-20))
#   left_arm(90, 50)            at 50% speed (speed is a percent, like drive)
#   arm_speed(left_up=100, left_down=40)   default speeds from now on: raise fast, lower slowly
#                               (right_up= / right_down= for the right arm; a number on one move still wins)
#   left_arm(90, fast=True)     quicker, a little less exact
#   left_arm(90, wait=False)    start the arm and go straight to the next command, so the arm moves
#                               while the robot drives or while the other arm moves
#   wait_for_arms()             wait until both arms have arrived
#   right_arm(45)               the same commands for the right arm: right_arm.by(-10), right_arm(45, 50) ...
#                               (set it up in robot_master.py first)
#   If an arm's motor is not plugged in at all, its commands are skipped (a NOTE says so).
#
#   --- OTHER ---
#   pause(ms)                   wait (1000 ms = 1 second)
#   wait_for_button()           wait until you press the LEFT hub button
#   finish()                    relax the arms and print how far off the heading is + the run summary
#
# DATA: every move prints a line starting with "LOG," (distance, each wheel, gyro, arm angle, time).
#   When you run from VS Code, each run is saved automatically to robot-data\runs\ as a CSV file and
#   shown in robot-data\dashboard.html. Column meanings: LOG NOTES in robot_master.py.
#
# Turns always count from where the robot is SUPPOSED to be facing, so small errors don't add up.
from pybricks.parameters import Button
from pybricks.tools import wait
from robot_master import make_drive, make_arm, home_arms, log_summary, gear_text, ATTACHMENTS, DRIVE_V, TURN_RATE
import robot_master as _rm

_drive = None
_arms = None
_speed = 100  # percent, changed by set_speed()
# Default arm speeds in percent, per arm and direction, changed by arm_speed().
_arm_speed = {"left_arm": {"up": 100, "down": 100}, "right_arm": {"up": 100, "down": 100}}
_gears = {}  # gear trains entered with gears(), used by start()
_homing = {}  # arm name -> True / False from left_arm.homing(...), used by start()
_robot_homing = [False]  # robot_homing(True): square on the wall behind the robot at start
ROBOT_HOMING_MAX_MM = 100  # robot_homing gives up after backing this far without touching a wall
_warned = []


def _before_start(what):
    if _drive:
        print("STOP:", what, "must come BEFORE start().")
        raise SystemExit


def gears(left=None, right=None):
    # Which gears are on each arm, in order from the MOTOR gear to the ARM gear. Put it BEFORE start().
    #   gears(left=[12, 36])                     motor 12T drives 36T on the arm
    #   gears(left=[20, [12, 12], 12])           two gears on the same axle go in brackets together
    # Leave an arm out (or None) to use the gears written in robot_master.py.
    _before_start("gears()")
    if left is not None:
        _gears["left_arm"] = left
    if right is not None:
        _gears["right_arm"] = right


def robot_homing(on=True):
    # robot_homing(True): at start, after the arms are homed, the robot backs slowly into the wall behind it
    # until both wheels touch, and that direction becomes heading 0. Put it BEFORE start().
    _before_start("robot_homing()")
    _robot_homing[0] = bool(on)


def start(name=""):
    # Builds the drive and arms, sets their gears, homes them (as asked) and lines the robot up on the wall
    # if robot_homing(True). Robot still, at base. Only does it once.
    # name = what the dashboard calls this run, e.g. start("Run 1"). Use the same name every time you test it.
    global _drive, _arms
    if _drive:
        return
    _rm.RUN_NAME = name
    _drive = make_drive()
    _arms = {}
    for n in ATTACHMENTS:
        try:
            _arms[n] = make_arm(n)
        except OSError:
            print("NOTE: no motor plugged into", n, "- its commands will be skipped this run")
    for n in _arms:
        a = _arms[n]
        if n in _gears:
            if not a.set_gears(_gears[n]):
                print("STOP: fix the gears for", n, "and run again.")
                raise SystemExit
        elif a.gears:
            print("GEARS", n, gear_text(a.gears), "(from robot_master.py)")
        else:
            print("GEARS", n, "none entered: angles are motor degrees")
        if n in _homing:
            a.do_home = _homing[n]
        if a.do_home:
            if a.min_deg is None and a.max_deg is None:
                print("NOTE:", n, "homing uses the direction in robot_master.py, which was never measured -",
                      "watch it the first time")
            print("HOMING", n, "on: lowering gently onto its stop")
        else:
            print("HOMING", n, "off: its position now counts as 0 - put it in its start position by hand")
    if not home_arms(_arms):
        print("STOP: an arm could not find its stop (see HOME FAILED above). Check it, or use .homing(False).")
        raise SystemExit
    if _robot_homing[0]:
        print("HOMING robot: backing gently into the wall behind it")
        # At most 10 cm: the robot starts close to the wall, and must not back out of base looking for one.
        if not _drive.square_to_wall(backwards=True, heading=0, max_mm=ROBOT_HOMING_MAX_MM):
            print("WARNING: no wall within", ROBOT_HOMING_MAX_MM // 10, "cm behind the robot - starting from where it is")
    print("READY")


def _d():
    if not _drive:
        start()
    return _drive


def _arm(name):
    if _arms is None:
        start()
    if name not in _arms:
        if name not in _warned:
            _warned.append(name)
            print("NOTE:", name, "has no motor - skipping its moves")
        return None
    return _arms[name]


def _pct(speed):
    # Percent to use for one move: the speed given, or the set_speed() value. Kept between 10 and 100
    # (100 is already near the motors' top speed, and faster turns overshoot).
    p = _speed if speed is None else speed
    if p > 100:
        print("speed", p, "is too high, using 100")
        return 100
    if p < 10:
        print("speed", p, "is too low, using 10")
        return 10
    return p


def set_speed(percent):
    # Speed for every move after this: 100 = normal, 50 = half. set_speed(100) to go back to normal.
    global _speed
    _speed = _pct(percent)


def drive(mm, speed=None):
    # + forward, - backward. speed = percent (100 = normal)
    _d().straight(mm, v=DRIVE_V * _pct(speed) / 100)


def turn(deg, speed=None):
    # + right (clockwise), - left. speed = percent (100 = normal)
    _d().turn(deg, rate=TURN_RATE * _pct(speed) / 100)


def forward(mm, speed=None):
    drive(abs(mm), speed)


def back(mm, speed=None):
    drive(-abs(mm), speed)


def turn_right(deg, speed=None):
    turn(abs(deg), speed)


def turn_left(deg, speed=None):
    turn(-abs(deg), speed)


def face(deg, speed=None):
    turn(deg - _d().target, speed)


def square():
    return _d().square_to_wall()


def arm_speed(left_up=None, left_down=None, right_up=None, right_down=None):
    # Default speed (percent) for every arm move after this, separately for going up and going down.
    #   arm_speed(left_down=40)            left arm lowers at 40%, everything else unchanged
    # A speed written on one move still wins: left_arm(90, 70).
    for name, d, v in (("left_arm", "up", left_up), ("left_arm", "down", left_down),
                       ("right_arm", "up", right_up), ("right_arm", "down", right_down)):
        if v is not None:
            _arm_speed[name][d] = _pct(v)


def _move_arm(name, deg, speed, wait, fast, by):
    a = _arm(name)
    if a is None:
        return
    if a.min_deg is None and a.max_deg is None and name + "-range" not in _warned:
        _warned.append(name + "-range")
        print("NOTE:", name, "has no safe range set in robot_master.py yet - it will move anywhere you ask")
    if by:
        deg = a.angle() + deg
    if speed is None:
        speed = _arm_speed[name]["up" if deg >= a.angle() else "down"]
    a.move_to(deg, "fast" if fast else None, wait_done=wait, speed_pct=_pct(speed))


class _ArmCommand:
    # One attachment arm: left_arm(90) goes to 90, left_arm.by(20) moves by 20, left_arm.homing(False)
    # switches homing off for this run. See the cheat sheet at the top.
    def __init__(self, name):
        self.name = name

    def __call__(self, deg, speed=None, wait=True, fast=False):
        _move_arm(self.name, deg, speed, wait, fast, False)

    def by(self, deg, speed=None, wait=True, fast=False):
        _move_arm(self.name, deg, speed, wait, fast, True)

    def homing(self, on=True):
        # True: home at start (lower gently onto the stop, call it 0). False: count where it is as 0.
        _before_start(self.name + ".homing()")
        _homing[self.name] = bool(on)


left_arm = _ArmCommand("left_arm")
right_arm = _ArmCommand("right_arm")


def left_arm_by(deg, speed=None, wait=True, fast=False):
    # Same as left_arm.by(...) - kept so older run files still work.
    _move_arm("left_arm", deg, speed, wait, fast, True)


def right_arm_by(deg, speed=None, wait=True, fast=False):
    # Same as right_arm.by(...) - kept so older run files still work.
    _move_arm("right_arm", deg, speed, wait, fast, True)


def wait_for_arms():
    # Waits until both arms have finished their moves (use after left_arm(..., wait=False)).
    # Returns True if both got there, False if one jammed (timed out).
    ok = True
    if _arms:
        for name in _arms:
            if not _arms[name].wait_done():
                ok = False
    return ok


def pause(ms):
    wait(ms)


def wait_for_button():
    hub = _d().hub
    print("Press the LEFT button")
    while Button.LEFT not in hub.buttons.pressed():
        wait(20)
    while Button.LEFT in hub.buttons.pressed():
        wait(20)
    wait(500)  # let your hand get clear


def finish():
    if _arms:
        wait_for_arms()  # let any arm still moving get there (and log it) before relaxing
        for name in _arms:
            _arms[name].release()
    if _drive:
        print("DONE, heading off by", round(_drive.error(), 1), "degrees")
        log_summary(_drive.hub)
