import numpy as np


#===================================================#
#                                                   #
#               Point cloud filtering               #
#                                                   #
#===================================================#

LIDAR_HEADING = 90

FIELD_OF_VIEW = 120

CONVOLUTION_SIZE = 31


#===================================================#
#                                                   #
#              Steer to PWM parameters              #
#                                                   #
#===================================================#

STEERING_LIMIT = 18.0

PWM_STEER_MIN = 5.2
PWM_STEER_MAX = 7.9

STEER2PWM_A = 0.5 * (PWM_STEER_MAX - PWM_STEER_MIN) / STEERING_LIMIT
STEER2PWM_B = 0.5 * (PWM_STEER_MAX + PWM_STEER_MIN)

STEER_FACTOR = np.array(
    [[0.00, 0.000],
     [10.0, 0.167],
     [20.0, 0.350],
     [30.0, 0.650],
     [40.0, 0.850],
     [50.0, 1.000]]
)

STEER_FACTOR[:, 1] *= STEERING_LIMIT


#===================================================#
#                                                   #
#              Speed to PWM parameters              #
#                                                   #
#===================================================#

PWM_SPEED_MIN = 7.6
PWM_SPEED_MAX = 7.8

SPEED2PWM_A = PWM_SPEED_MAX - PWM_SPEED_MIN
SPEED2PWM_B = PWM_SPEED_MIN

SPEED_FACTOR = np.array(
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


#===================================================#
#                                                   #
#                Reverse parameters                 #
#                                                   #
#===================================================#

WIDTH = 0.20

MIN_HEIGHT = 0.35
MAX_HEIGHT = 0.50

HEIGHT_FACTOR = np.array(
    [[0.00, 0.00],
     [0.80, 0.30],
     [1.50, 1.00]]
)

HEIGHT_FACTOR[:, 1] = MIN_HEIGHT + (MAX_HEIGHT - MIN_HEIGHT) * HEIGHT_FACTOR[:, 1]

PWM_REVERSE = 6.5
