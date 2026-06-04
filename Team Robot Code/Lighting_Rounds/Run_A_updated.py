from robot_base import hub, RAM, LAM, make_robot, left_motor, right_motor
from pybricks.parameters import Stop

# Run_A uses axle_track=101.6 — passed directly to make_robot().
# make_robot() calls robot.reset() internally (safe Pybricks v3.6+ way).
robot = make_robot(axle_track=101.6)

left_motor.control.limits(speed=800)
right_motor.control.limits(speed=800)

robot.settings(
    straight_speed=850,
    straight_acceleration=(200, 700),  # ramp up gently (300), brake fast (500)
    turn_rate=620,
    turn_acceleration=450
)

robot.heading_control.pid(21242, 0, 5310, 4, 8)

# -------------lightning round 1st run!!!!!!!!!!!!!!!!!-------
###------------- run 2 & 3 remains the same -----------------------
if hub.imu.ready():
    print(robot.heading_control.pid())

    robot.straight(690)
    robot.arc(-200, 15)
    robot.straight(31)

    # SOLVING MISSION 5
    robot.turn(30)
    robot.straight(-80)

    # SOLVING MISSION 7
    robot.turn(35)
    print(hub.imu.heading())
    # ARM DROP
    RAM.run_time(-1000,890)
    robot.straight(130)
    # ARM PICKUP
    RAM.run_time(1500,890)

    robot.straight(-71) #tune if you are getting stuck on the boulder misssion
    
    # SOLVING MISSION 7
    robot.turn(-130)

    #SOLVING MISSION 8
    robot.straight(-200)#tune if you are not hitting the lever on mission 8
    # # FIRST HIT
    LAM.run_time(-500,1200)
    LAM.run_time(200,1200)
    # SECOND HIT
    LAM.run_time(-1500,1200)
    LAM.run_time(1200,1200)
    # THIRD HIT
    LAM.run_time(-1500,1200)
    LAM.run_time(1200,1200)
    # HEADING BACK HOME
    robot.settings(
    straight_speed=950,
    straight_acceleration=(500, 800),  # ramp up gently (300), brake fast (500)
    turn_rate=820,
    turn_acceleration=750
)

    robot.straight(150,Stop.NONE)
    robot.turn(-80,Stop.NONE)
    robot.straight(800)
