from config import *
import numpy as np

cfg = None

def load_constants(new_filepath="config.json"):
    """
    Reloads the configuration and updates all constants.
    
    Optionally, a new configuration file path can be provided.
    """
    
    if(new_filepath != "config.json"):
        print(f"Loading constants from configuration file {new_filepath}")
        
        
    global cfg
    global NOM_VOITURE
    
    global LIDAR_BAUDRATE, LIDAR_HEADING_OFFSET_DEG, LIDAR_POINT_TIMEOUT_MS, LIDAR_FOV_FILTER
    global FIELD_OF_VIEW_DEG, CONVOLUTION_SIZE
    
    global AVOID_CORNER_MAX_ANGLE, AVOID_CORNER_MIN_DISTANCE, AVOID_CORNER_SCALE_FACTOR
    
    global STEERING_LIMIT, DC_STEER_MIN, DC_STEER_MAX, STEER_VARIATION_RATE, STEER_CENTER, STEER_FACTOR
    
    global TICKS_TO_METER, APERTURE_ANGLE, DC_SPEED_MIN, DC_SPEED_MAX, SPEED2DC_A, SPEED2DC_B
    global SPEED_FACTOR_DIST, SPEED_FACTOR_ANG, AGGRESSIVENESS
    
    global HITBOX_H1, HITBOX_H2, HITBOX_W
    
    global MIN_LENGTH, MAX_LENGTH, LERP_MAP_LENGTH
    global MIN_POINTS_TO_TRIGGER, REVERSE_CHECK_COUNTER, PWM_REVERSE, STEERING_LIMIT_IN_REVERSE

    # Load configuration from the current config file path.
    cfg = load_config(new_filepath)

    #------------------------------------------------#
    #            General Car Information             #
    #------------------------------------------------#
    NOM_VOITURE = get_config_value(cfg, "NOM_VOITURE", "Voiture-Couleur")

    #------------------------------------------------#
    #          Point Cloud Filtering Settings        #
    #------------------------------------------------#
    LIDAR_BAUDRATE = int(get_config_value(cfg, "LIDAR_BAUDRATE", 115200))
    LIDAR_HEADING_OFFSET_DEG = int(get_config_value(cfg, "LIDAR_HEADING_OFFSET_DEG", -90))
    LIDAR_POINT_TIMEOUT_MS = int(get_config_value(cfg, "LIDAR_POINT_TIMEOUT_MS", 1000))
    LIDAR_FOV_FILTER = int(get_config_value(cfg, "LIDAR_FOV_FILTER", 180))  # excludes backward readings
    FIELD_OF_VIEW_DEG = int(get_config_value(cfg, "FIELD_OF_VIEW_DEG", 120))
    CONVOLUTION_SIZE = int(get_config_value(cfg, "CONVOLUTION_SIZE", 31))

    #------------------------------------------------#
    #          Avoid Corner Parameters               #
    #------------------------------------------------#
    AVOID_CORNER_MAX_ANGLE = int(get_config_value(cfg, "AVOID_CORNER_MAX_ANGLE", 8))
    AVOID_CORNER_MIN_DISTANCE = float(get_config_value(cfg, "AVOID_CORNER_MIN_DISTANCE", 2.5))
    AVOID_CORNER_SCALE_FACTOR = float(get_config_value(cfg, "AVOID_CORNER_SCALE_FACTOR", 1.2))

    #------------------------------------------------#
    #         Steer to PWM Parameters                #
    #------------------------------------------------#
    STEERING_LIMIT = float(get_config_value(cfg, "STEERING_LIMIT", 18.0))
    DC_STEER_MIN = float(get_config_value(cfg, "DC_STEER_MIN", 5.0))
    DC_STEER_MAX = float(get_config_value(cfg, "DC_STEER_MAX", 10.0))
    STEER_VARIATION_RATE = 0.5 * (DC_STEER_MAX - DC_STEER_MIN) / STEERING_LIMIT
    STEER_CENTER = 0.5 * (DC_STEER_MAX + DC_STEER_MIN)
    STEER_FACTOR = np.array([
        [0.00, 0.000],
        [10.0, 0.167],
        [20.0, 0.360],
        [30.0, 0.680],
        [40.0, 0.900],
        [50.0, 1.000]
    ])
    
    STEER_FACTOR[:, 1] *= STEERING_LIMIT

    #------------------------------------------------#
    #         Speed to PWM Parameters                #
    #------------------------------------------------#
    
    TICKS_TO_METER = int(get_config_value(cfg, "TICKS_TO_METER", 213)) #CONVERTS INTERRUPT SPEED TO M/S
    
    APERTURE_ANGLE = int(get_config_value(cfg, "APERTURE_ANGLE", 20))
    DC_SPEED_MIN = float(get_config_value(cfg, "DC_SPEED_MIN", 7.6))
    DC_SPEED_MAX = float(get_config_value(cfg, "DC_SPEED_MAX", 8.2))
    
    SPEED2DC_A = DC_SPEED_MAX - DC_SPEED_MIN
    SPEED2DC_B = DC_SPEED_MIN
    
    SPEED_FACTOR_DIST = np.array([
        [0.00, 0.00],
        [0.25, 0.10],
        [0.50, 0.15],
        [0.75, 0.20],
        [1.00, 0.30],
        [1.25, 0.50],
        [1.50, 0.70],
        [1.75, 0.90],
        [2.00, 1.00]
    ])
    SPEED_FACTOR_ANG = np.array([
        [0.00, 1.500],
        [10.0, 1.200],
        [20.0, 1.000],
        [30.0, 0.950],
        [40.0, 0.900],
        [50.0, 0.900]
    ])
    AGGRESSIVENESS = float(get_config_value(cfg, "AGGRESSIVENESS", 0.7))


    #------------------------------------------------#
    #                Hitbox Parameters               #
    #------------------------------------------------#
    
    HITBOX_H1 = float(get_config_value(cfg, "HITBOX_H1", 0.11))
    HITBOX_H2 = float(get_config_value(cfg, "HITBOX_H2", 0.31))
    HITBOX_W  = float(get_config_value(cfg, "HITBOX_W", 0.11)) 

    #------------------------------------------------#
    #           Reverse Parameters                   #
    #------------------------------------------------#
    
    
    MIN_LENGTH = float(get_config_value(cfg, "MIN_LENGTH", 0.28))
    MAX_LENGTH = float(get_config_value(cfg, "MAX_LENGTH", 0.38))
    LERP_MAP_LENGTH = np.array([
        [0.00, 0.00],
        [0.80, 0.30],
        [1.50, 1.00]
    ])
    MIN_POINTS_TO_TRIGGER = int(get_config_value(cfg, "MIN_POINTS_TO_TRIGGER", 8))
    REVERSE_CHECK_COUNTER = int(get_config_value(cfg, "REVERSE_CHECK_COUNTER", 8))
    LERP_MAP_LENGTH[:, 1] = MIN_LENGTH + (MAX_LENGTH - MIN_LENGTH) * LERP_MAP_LENGTH[:, 1]
    PWM_REVERSE = 6.3
    STEERING_LIMIT_IN_REVERSE = STEERING_LIMIT

load_constants()