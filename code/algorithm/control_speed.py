from algorithm.constants import *
import numpy as np

def compute_speed(convoluted_lidar, target_angle: float):
    MIN_SPEED = 0.7  # Minimum speed for curves
    MAX_SPEED = 1.6  # Maximum speed for straight paths
    
    angle_magnitude = abs(target_angle)
    
    # Create a smooth transition - exponential decay works well for this
    # As angle increases, speed decreases toward MIN_SPEED
    # Parameter tuning - adjust the 0.02 to control how quickly speed drops with angle
    decay_factor = 0.03
    
    speed = MAX_SPEED * np.exp(-decay_factor * angle_magnitude)
    
    speed = max(speed, MIN_SPEED)
    speed = min(speed, MAX_SPEED)
    
    return speed