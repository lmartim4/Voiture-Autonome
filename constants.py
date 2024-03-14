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

PWM_LEF = 5.4
PWM_RIG = 7.9

STEER2PWM_A = 0.5 * (PWM_RIG - PWM_LEF) / STEERING_LIMIT
STEER2PWM_B = 0.5 * (PWM_RIG + PWM_LEF)

STEER_FACTOR = np.array(
    [[0.00, 0.000],
     [10.0, 0.167],
     [20.0, 0.350],
     [30.0, 0.700],
     [40.0, 1.000],
     [50.0, 1.000]]
)

STEER_FACTOR[:, 1] *= STEERING_LIMIT


#===================================================#
#                                                   #
#              Speed to PWM parameters              #
#                                                   #
#===================================================#

PWM_MIN = 8.1
PWM_MAX = 8.3

SPEED2PWM_A = PWM_MAX - PWM_MIN
SPEED2PWM_B = PWM_MIN

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
