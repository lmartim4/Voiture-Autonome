import numpy as np


#===================================================#
#                                                   #
#               Point cloud filtering               #
#                                                   #
#===================================================#

LIDAR_HEADING =  90   # int: degrees [°]

FIELD_OF_VIEW = 120   # int: degrees [°]

CONVOLUTION_SIZE = 31


#===================================================#
#                                                   #
#              Avoid corner parameters              #
#                                                   #
#===================================================#

AVOID_CORNER_MAX_ANGLE = 8   # int: degress [°]

AVOID_CORNER_MIN_DISTANCE = 2.5   # float: meters [m]

AVOID_CORNER_SCALE_FACTOR = 1.2   # float: number


#===================================================#
#                                                   #
#           Steer actuator PWM parameters           #
#                                                   #
#===================================================#

STEERING_LIMIT = 18.0   # float: degrees [°]

DC_STEER_MIN = 5.3   # float: duty cycle
DC_STEER_MAX = 7.9   # float: duty cycle

STEER2DC_A = 0.5 * (DC_STEER_MAX - DC_STEER_MIN) / STEERING_LIMIT
STEER2DC_B = 0.5 * (DC_STEER_MAX + DC_STEER_MIN)

LERP_MAP_STEER = np.array(
    [[0.00, 0.000],
     [10.0, 0.167],
     [20.0, 0.360],
     [30.0, 0.680],
     [40.0, 0.900],
     [50.0, 1.000]]
)

# Maps float: degrees [°] to float: degrees [°]
LERP_MAP_STEER[:, 1] = LERP_MAP_STEER[:, 1] * STEERING_LIMIT


#===================================================#
#                                                   #
#           Speed actuator PWM parameters           #
#                                                   #
#===================================================#

APERTURE_ANGLE = 20   # int: degrees [°]

DC_SPEED_MIN = 7.6   # float: duty cycle
DC_SPEED_MAX = 8.6   # float: duty cycle

SPEED2DC_A = DC_SPEED_MAX - DC_SPEED_MIN
SPEED2DC_B = DC_SPEED_MIN

# Maps float: meters [m] to float: number
LERP_MAP_SPEED_DIST = np.array(
    [[0.00, 0.00],
     [0.25, 0.10],
     [0.50, 0.15],
     [0.75, 0.20],
     [1.00, 0.30],
     [1.25, 0.50],
     [1.50, 0.70],
     [1.75, 0.90],
     [2.00, 1.00]]
)

# Maps float: degrees [°] to float: number
LERP_MAP_SPEED_ANGL = np.array(
    [[0.00, 1.500],
     [10.0, 1.200],
     [20.0, 1.000],
     [30.0, 0.950],
     [40.0, 0.900],
     [50.0, 0.900]]
)

AGGRESSIVENESS = 0.3   # float: number between 0.0 and 1.0


#===================================================#
#                                                   #
#                Reverse parameters                 #
#                                                   #
#===================================================#

WIDTH = 0.20   # float: meters [m]

MIN_LENGTH = 0.28   # float: meters [m]
MAX_LENGTH = 0.38   # float: meters [m]

LERP_MAP_LENGTH = np.array(
    [[0.00, 0.00],
     [0.80, 0.30],
     [1.50, 1.00]]
)

# Maps float: speed [m/s] to float: meters [m]
LERP_MAP_LENGTH[:, 1] = LERP_MAP_LENGTH[:, 1] * (MAX_LENGTH - MIN_LENGTH)
LERP_MAP_LENGTH[:, 1] = LERP_MAP_LENGTH[:, 1] + MIN_LENGTH

MIN_POINTS_TO_TRIGGER = 8   # int: number

REVERSE_CHECK_COUNTER = 8   # int: number

DC_REVERSE = 6.3   # float: duty cycle

STEER_IN_REVERSE = 0.7 * STEERING_LIMIT   # float: degrees [°]
