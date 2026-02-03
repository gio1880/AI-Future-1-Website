import math
import matplotlib.pyplot as plt

scan = [
    {'back_mm': 2000, 'angle_index': 0, 'front_mm': 2000},
    {'back_mm': 2000, 'angle_index': -1, 'front_mm': 2000},
    {'back_mm': 2000, 'angle_index': -2, 'front_mm': 402},
    {'back_mm': 2000, 'angle_index': -3, 'front_mm': 428},
    {'back_mm': 2000, 'angle_index': -4, 'front_mm': 2000},
    {'back_mm': 2000, 'angle_index': -5, 'front_mm': 1149},
    {'back_mm': 2000, 'angle_index': -6, 'front_mm': 150},
    {'back_mm': 296,  'angle_index': 0, 'front_mm': 2000},
    {'back_mm': 2000, 'angle_index': 1, 'front_mm': 2000},
    {'back_mm': 2000, 'angle_index': 2, 'front_mm': 333},
    {'back_mm': 2000, 'angle_index': 3, 'front_mm': 2000},
    {'back_mm': 2000, 'angle_index': 4, 'front_mm': 1141},
    {'back_mm': 2000, 'angle_index': 5, 'front_mm': 1124},
    {'back_mm': 2000, 'angle_index': 6, 'front_mm': 190},
]

# --- TUNE THIS ---
# angle_index isn't degrees; it's a step counter.
# If your robot turned ~90 degrees total from leftmost to rightmost:
#   angle_step_deg ≈ 90 / steps_each_side
# In your scan you went from -6..+6, so steps_each_side=6 => ~15 deg per step.
ANGLE_STEP_DEG = 15

# Treat these as "no hit"
NO_HIT_MM = 2000

front_x, front_y = [], []
back_x, back_y = [], []

for s in scan:
    a_deg = s["angle_index"] * ANGLE_STEP_DEG

    # FRONT points (in front of robot)
    rf = s["front_mm"]
    if rf is not None and rf < NO_HIT_MM:
        th = math.radians(a_deg)
        front_x.append(rf * math.cos(th))
        front_y.append(rf * math.sin(th))

    # BACK points (behind robot)
    # Behind means 180 degrees opposite direction
    rb = s["back_mm"]
    if rb is not None and rb < NO_HIT_MM:
        th = math.radians(a_deg + 180)
        back_x.append(rb * math.cos(th))
        back_y.append(rb * math.sin(th))

plt.figure()
plt.scatter(front_x, front_y, marker="o", label="Front sensor hits")
plt.scatter(back_x, back_y, marker="x", label="Back sensor hits")
plt.scatter([0], [0], marker="s", label="Robot (0,0)")

plt.axis("equal")
plt.grid(True)
plt.xlabel("mm forward (x)")
plt.ylabel("mm sideways (y)")
plt.title("Distance Scan Point Cloud")
plt.legend()
plt.show()
