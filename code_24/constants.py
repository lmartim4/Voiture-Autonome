from config import *
import numpy as np

cfg = load_config()

NOM_VOITURE = get_config_value(cfg, "NOM_VOITURE", "Voiture-Couleur")

#===================================================#
#                                                   #
#               Point cloud filtering               #
#                                                   #
#===================================================#

LIDAR_BAUDRATE = int(get_config_value(cfg, "LIDAR_BAUDRATE", 115200))
LIDAR_HEADING_OFFSET_DEG = int(get_config_value(cfg, "LIDAR_HEADING_OFFSET_DEG", -90))

LIDAR_FOV_FILTER = int(get_config_value(cfg , "LIDAR_FOV_FILTER", 180)) #EXLUDES BACKWARDS READINGS

FIELD_OF_VIEW_DEG = int(get_config_value(cfg, "FIELD_OF_VIEW_DEG", 120))
CONVOLUTION_SIZE = int(get_config_value(cfg, "CONVOLUTION_SIZE",   31))

#===================================================#
#                                                   #
#              Avoid corner parameters              #
#                                                   #
#===================================================#

AVOID_CORNER_MAX_ANGLE = int(get_config_value(cfg, "AVOID_CORNER_MAX_ANGLE", 8))            # int: degress [°]
AVOID_CORNER_MIN_DISTANCE = float(get_config_value(cfg, "AVOID_CORNER_MIN_DISTANCE", 2.5))  # float: meters [m]
AVOID_CORNER_SCALE_FACTOR = float(get_config_value(cfg, "AVOID_CORNER_SCALE_FACTOR",1.2))   # float: number

#===================================================#
#                                                   #
#              Steer to PWM parameters              #
#                                                   #
#===================================================#

#  In a standard servo control setup, the signal has a total
#  period of 20 ms, which corresponds to a frequency of 50 Hz.
#  A 1 ms “ON” pulse during that 20 ms frame is 5% of the total
#  cycle (1 ms ÷ 20 ms × 100%), whereas a 2 ms pulse is 10% (2 ms ÷ 20 ms × 100%).
#  In other words, going from 1 ms to 2 ms within each 20 ms cycle corresponds
#  roughly to rotating the servo horn from one extreme to the other.

STEERING_LIMIT = float(get_config_value(cfg, "STEERING_LIMIT", 18.0)) # float: degrees [°]
DC_STEER_MIN =  float(get_config_value(cfg, "DC_STEER_MIN",  5.0))    # float: duty cycle
DC_STEER_MAX =  float(get_config_value(cfg, "DC_STEER_MAX",  10.0))   # float: duty cycle

STEER_VARIATION_RATE = 0.5 * (DC_STEER_MAX - DC_STEER_MIN) / STEERING_LIMIT
STEER_CENTER = 0.5 * (DC_STEER_MAX + DC_STEER_MIN)

print(STEER_VARIATION_RATE, STEER_CENTER)

STEER_FACTOR = np.array(
    [[0.00, 0.000],
     [5.0, 0.167],
     [10.0, 0.360],
     [15.0, 0.680],
     [20.0, 0.900],
     [25.0, 1.000]]
)

STEER_FACTOR[:, 1] *= STEERING_LIMIT

#===================================================#
#                                                   #
#              Speed to PWM parameters              #
#                                                   #
#===================================================#

APERTURE_ANGLE = int(get_config_value(cfg , "APERTURE_ANGLE", 20))

DC_SPEED_MIN = float(get_config_value(cfg , "DC_SPEED_MIN", 7.6))
DC_SPEED_MAX = float(get_config_value(cfg , "DC_SPEED_MAX", 8.2))

SPEED2DC_A = DC_SPEED_MAX - DC_SPEED_MIN
SPEED2DC_B = DC_SPEED_MIN

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

AGGRESSIVENESS = float(get_config_value(cfg, "AGGRESSIVENESS", 0.7))   # float: number between 0.0 and 1.0

#===================================================#
#                                                   #
#                Reverse parameters                 #
#                                                   #
#===================================================#

HITBOX_WIDTH =  float(get_config_value(cfg, "HITBOX_WIDTH", 0.20))
HITBOX_HEIGHT = float(get_config_value(cfg, "HITBOX_HEIGHT", 0.20))

MIN_LENGTH = float(get_config_value(cfg, "MIN_LENGTH", 0.28))
MAX_LENGTH = float(get_config_value(cfg, "MAX_LENGTH", 0.38))

LERP_MAP_LENGTH = np.array(
    [[0.00, 0.00],
     [0.80, 0.30],
     [1.50, 1.00]])

MIN_POINTS_TO_TRIGGER = int(get_config_value(cfg, "MIN_POINTS_TO_TRIGGER", 8))
REVERSE_CHECK_COUNTER = int(get_config_value(cfg, "REVERSE_CHECK_COUNTER", 8))

LERP_MAP_LENGTH[:, 1] = MIN_LENGTH + (MAX_LENGTH - MIN_LENGTH) * LERP_MAP_LENGTH[:, 1]
#PWM_REVERSE = np.interp(WIDTH, LERP_MAP_LENGTH[:, 0], LERP_MAP_LENGTH[:, 1])

PWM_REVERSE = 6.3

STEERING_LIMIT_IN_REVERSE = STEERING_LIMIT # float: degrees [°]