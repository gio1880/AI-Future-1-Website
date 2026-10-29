from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Port, Direction
from pybricks.tools import StopWatch, wait

# ---------------- Hub and motors ----------------
hub = PrimeHub()
left_motor = Motor(Port.A, Direction.COUNTERCLOCKWISE)
right_motor = Motor(Port.E, Direction.CLOCKWISE)

# ---------------- Robot constants ----------------
WHEEL_DIAMETER = 56        # mm
AXLE_TRACK = 122           # mm
WHEEL_CIRC = 3.1416 * WHEEL_DIAMETER
DEG_PER_MM = 360 / WHEEL_CIRC

# ---------------- PID constants ----------------
DIST_KP = 1.3
DIST_KD = 0.08
HEAD_KP = 0.7
HEAD_KD = 0.03

# ---------------- Feedforward ----------------
FF_SPEED = 300  # deg/s constant feedforward

# ---------------- Limits ----------------
MAX_SPEED = 900
MIN_SPEED = 120
MAX_DELTA_SPEED = 25
MAX_TURN = 50
DIST_DEADBAND = 3
HEAD_DEADBAND = 2

LEFT_TRIM = 1.0
RIGHT_TRIM = 1.0

# ---------------- Drive function ----------------
def drive_straight(distance_mm, target_heading=0):
    # Reset motors and heading
    left_motor.reset_angle(0)
    right_motor.reset_angle(0)
    hub.imu.reset_heading(0)

    last_dist_error = distance_mm * DEG_PER_MM
    last_head_error = 0
    last_forward = 0
    last_time = 0

    stopwatch = StopWatch()
    stopwatch.reset()

    print("Starting drive...")

    # Determine motion direction
    direction = 1 if distance_mm > 0 else -1
    distance_deg = abs(distance_mm * DEG_PER_MM)

    while True:
        now = stopwatch.time() / 1000  # seconds
        dt = now - last_time
        if dt == 0:
            dt = 0.01

        # --- Distance calculation ---
        avg_angle = (abs(left_motor.angle()) + abs(right_motor.angle())) / 2
        dist_error = distance_deg - avg_angle

        # Stop if within deadband
        if dist_error <= DIST_DEADBAND:
            break

        # Distance derivative
        dist_derivative = (dist_error - last_dist_error) / dt

        # Forward speed = feedforward + PID
        forward = direction * FF_SPEED + DIST_KP * dist_error + DIST_KD * dist_derivative

        # Clamp forward speed
        forward = max(min(forward, MAX_SPEED), -MAX_SPEED)
        if abs(forward) < MIN_SPEED:
            forward = MIN_SPEED * direction

        # Smooth acceleration
        forward = max(min(forward, last_forward + MAX_DELTA_SPEED), last_forward - MAX_DELTA_SPEED)
        last_forward = forward

        # --- Heading correction ---
        heading = hub.imu.heading()
        head_error = target_heading - heading
        head_derivative = (head_error - last_head_error) / dt
        turn = HEAD_KP * head_error + HEAD_KD * head_derivative
        turn = max(min(turn, MAX_TURN), -MAX_TURN)

        # Stop small corrections
        if abs(head_error) < HEAD_DEADBAND:
            turn = 0

        # --- Motor commands ---
        left_motor.run((forward - turn) * LEFT_TRIM)
        right_motor.run((forward + turn) * RIGHT_TRIM)

        # Debug
        print(f"DistErr: {int(dist_error)}  HeadErr: {int(head_error)}  Fwd: {int(forward)}  Turn: {int(turn)}")

        # Update
        last_dist_error = dist_error
        last_head_error = head_error
        last_time = now

        wait(20)

    # Stop motors
    left_motor.stop()
    right_motor.stop()
    print("Drive complete!", "Left:", left_motor.angle(), "Right:", right_motor.angle(), "Heading:", hub.imu.heading())
def turn_degrees(angle_deg):
    """
    Turn in place using gyro PD control with smooth acceleration.
    Positive angle = right turn
    Negative angle = left turn
    """

    # Reset gyro
    hub.imu.reset_heading(0)

    # PID constants for turning
    TURN_KP = 3.5
    TURN_KD = 0.25

    # Limits
    MAX_TURN_SPEED = 500
    MIN_TURN_SPEED = 120
    MAX_DELTA_TURN = 25
    ANGLE_DEADBAND = 2

    last_error = angle_deg
    last_turn = 0
    last_time = 0

    stopwatch = StopWatch()
    stopwatch.reset()

    print("Starting turn...")

    while True:
        now = stopwatch.time() / 1000
        dt = now - last_time
        if dt == 0:
            dt = 0.01

        # Current heading
        heading = hub.imu.heading()/10
        error = angle_deg - heading

        # Stop condition
        if abs(error) <= ANGLE_DEADBAND:
            break

        # Derivative
        derivative = (error - last_error) / dt

        # PD turn output
        turn = TURN_KP * error + TURN_KD * derivative

        # Clamp turn speed
        turn = max(min(turn, MAX_TURN_SPEED), -MAX_TURN_SPEED)

        # Minimum speed so it doesn't stall
        if abs(turn) < MIN_TURN_SPEED:
            turn = MIN_TURN_SPEED * (1 if turn > 0 else -1)

        # Smooth acceleration
        turn = max(min(turn, last_turn + MAX_DELTA_TURN), last_turn - MAX_DELTA_TURN)
        last_turn = turn

        # Scale down near target to prevent jerk
        turn *= min(1, abs(error) / 25)

        # Apply motors (turn in place)
        left_motor.run(-turn)
        right_motor.run(turn)

        # Debug
        print(f"TurnErr: {int(error)}  Turn: {int(turn)}")

        last_error = error
        last_time = now

        wait(20)

    # Stop motors
    left_motor.stop()
    right_motor.stop()
    print("Turn complete! Heading:", hub.imu.heading())

# ---------------- Example usage ----------------
# drive_straight(300)   # Forward 300 mm
turn_degrees(900)
# drive_straight(-200) # Backward 200 mm
