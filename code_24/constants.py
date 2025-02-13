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
#              Steer to PWM parameters              #
#                                                   #
#===================================================#

STEERING_LIMIT = 18.0

PWM_STEER_MIN = 5.3
PWM_STEER_MAX = 7.9

STEER2PWM_A = 0.5 * (PWM_STEER_MAX - PWM_STEER_MIN) / STEERING_LIMIT
STEER2PWM_B = 0.5 * (PWM_STEER_MAX + PWM_STEER_MIN)

STEER_FACTOR = np.array(
    [[0.00, 0.000],
     [10.0, 0.167],
     [20.0, 0.360],
     [30.0, 0.680],
     [40.0, 0.900],
     [50.0, 1.000]]
)

STEER_FACTOR[:, 1] *= STEERING_LIMIT


#===================================================#
#                                                   #
#              Speed to PWM parameters              #
#                                                   #
#===================================================#

PWM_SPEED_MIN = 7.6
PWM_SPEED_MAX = 8.6

SPEED2PWM_A = PWM_SPEED_MAX - PWM_SPEED_MIN
SPEED2PWM_B = PWM_SPEED_MIN

SPEED_FACTOR_DIST = np.array(
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

SPEED_FACTOR_ANG = np.array(
    [[0.00, 1.500],
     [10.0, 1.200],
     [20.0, 1.000],
     [30.0, 0.950],
     [40.0, 0.900],
     [50.0, 0.900]]
)


#===================================================#
#                                                   #
#                Reverse parameters                 #
#                                                   #
#===================================================#

WIDTH = 0.20

MIN_HEIGHT = 0.28
MAX_HEIGHT = 0.38

HEIGHT_FACTOR = np.array(
    [[0.00, 0.00],
     [0.80, 0.30],
     [1.50, 1.00]]
)

HEIGHT_FACTOR[:, 1] = MIN_HEIGHT + (MAX_HEIGHT - MIN_HEIGHT) * HEIGHT_FACTOR[:, 1]

PWM_REVERSE = 6.3
