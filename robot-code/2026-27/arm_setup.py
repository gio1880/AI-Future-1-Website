# arm_setup.py -- measures one arm on the robot and prints its settings line for robot_master.py.
# For coaches. About one minute. Run it from VS Code like any run file and watch the arm the whole time;
# the hub's center button stops it.
#
# What it does:
#   1. You put the arm where it normally starts a run and press the LEFT hub button.
#   2. It moves slowly (60 deg/s, limited push) toward one end until it touches the stop.
#   3. It moves slowly the other way until the other stop (or 720 motor degrees), logging the load.
#   4. It goes back to the start position and prints the ATTACHMENTS line to paste into robot_master.py.
# Run it 2-3 times: the numbers should agree within a few degrees.
from pybricks.hubs import PrimeHub
from pybricks.parameters import Button
from pybricks.tools import wait
import robot_master as rm
from robot_master import make_arm, measure_travel, ATTACHMENTS, gear_text, _rnd

ARM = "right_arm"  # "right_arm" or "left_arm"
# MOTOR direction toward the stop to home on = the arm's home_dir in robot_master.py. (2026-10-28: the right arm
# was first measured toward -1, the far stop 125 motor deg away; its homing now goes to the near stop, +1.)
TOWARD_STOP = ATTACHMENTS[ARM]["home_dir"]
MARGIN = 5  # arm degrees kept away from each stop in min_deg / max_deg
# Push used to find the stops (mNm), still slow at 60 deg/s. 50 was too weak on 2026-10-27: the right arm did not
# move at all one way and stuck after 24 deg the other way, though missions move it 75+ deg. 100 got the left arm
# past its stiff spot in October.
PUSH = 100

hub = PrimeHub()
rm.RUN_NAME = "Arm setup " + ARM
c = ATTACHMENTS[ARM]
arm = make_arm(ARM)
arm.min_deg = None  # no limits while measuring
arm.max_deg = None
# An arm that never homed keeps its usual START position as 0 (so the numbers in run files stay the same);
# an arm that already homes keeps its stop as 0.
keep_start_zero = (not c.get("home", False)) or c.get("start_deg") == 0

print("SETUP", ARM, "| gears", gear_text(arm.gears) if arm.gears else "none (angles = motor degrees)")
print("1. Put the arm by hand where it normally starts a run. Then press the LEFT hub button and let go.")
while Button.LEFT not in hub.buttons.pressed():
    wait(20)
while Button.LEFT in hub.buttons.pressed():
    wait(20)
wait(800)
arm.zero()  # start position = 0 while measuring

print("2. Moving slowly toward the first stop...")
found, travel = arm.home(direction=TOWARD_STOP, torque=PUSH, max_travel=400, reset=False)
if not found:
    arm.release()
    print("SETUP STOP: no stop within 400 motor degrees that way. Set TOWARD_STOP =", -TOWARD_STOP, "and run again.")
    raise SystemExit
# The stop while PUSHING on it (home_ref="pushed" homing counts it the same way); the arm springs back a little after.
stop_a = travel / arm.gear * arm.sign  # arm degrees from the start position
print("   first stop at", _rnd(stop_a, 1), "arm deg from the start position while pushing (motor moved", int(travel),
      "deg; it rests at", _rnd(arm.angle(), 1), "after letting go)")
if abs(travel) < 3:
    print("   NOTE: it did not move that way at all - it started resting on that stop, or something holds it.",
          "If it should have moved, check what blocks it.")
wait(300)

print("3. Moving slowly toward the other end...")
found_b, travel_b, marks = measure_travel(arm, -TOWARD_STOP, max_travel=720, speed=60, torque=PUSH, mark=10)
stop_b = arm.angle()
print("   other end at", _rnd(stop_b, 1), "arm deg", "(stop)" if found_b else "(NO stop found within 720 motor deg)")
print("   load along the way (motor deg, speed, mNm):", marks)
heavy = [m for m in marks if abs(m[2]) > PUSH * 0.6]
if heavy:
    print("   NOTE: stiff spots (load > 60 mNm) at", [m[0] for m in heavy], "- check nothing rubs there")

print("4. Back to the start position.")
arm.move_to(0, speed_pct=50)
arm.release()

# Settings line. Angles relative to the start position (keep_start_zero) or to the first stop.
base = 0 if keep_start_zero else stop_a
a, b = stop_a - base, stop_b - base
lo, hi = min(a, b), max(a, b)
min_deg = int(lo + MARGIN + 0.5) if (found_b or lo == a) else None
max_deg = int(hi - MARGIN) if (found_b or hi == a) else None
offset = int(round(a))
gears_txt = str(c.get("gears"))
port = "Port." + ("F" if ARM == "right_arm" else "B")
print("SETUP RESULT", ARM, "| first stop", _rnd(a, 1), "| other end", _rnd(b, 1), "| travel", _rnd(hi - lo, 1),
      "arm deg")
if hi - lo < 2 * MARGIN + 20:
    print("SETUP STOP: only", _rnd(hi - lo, 1), "deg of travel - it probably stuck on something before a real stop.",
          "Free the arm and run again. No settings line printed.")
    raise SystemExit
print("SETUP LINE - put this in ATTACHMENTS in robot_master.py (check port, gears and sign are right):")
print('    "' + ARM + '": dict(port=' + port + ", gears=" + gears_txt + ", sign=" + str(c["sign"]) +
      ", home_dir=" + str(TOWARD_STOP) + ', home_ref="pushed", home_offset=' + str(offset if keep_start_zero else 0) +
      ", home_torque=" + str(PUSH) + (", start_deg=0" if keep_start_zero else "") +
      ", min_deg=" + str(min_deg) + ", max_deg=" + str(max_deg) + ', profile="precise", home=True),')
if not found_b:
    print("SETUP NOTE: no second stop - the limit on that side is a guess. Measure it with a protractor.")
print("SETUP DONE. Run it 2-3 times; the numbers should agree within a few degrees.")
