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

def compute_speed2(convoluted_lidar, target_angle: float, 
                  min_speed=0.7, max_speed=1.6, 
                  look_ahead_width=5, distance_influence=0.5,
                  max_safe_distance=8.0, min_safe_distance=2.0):
    """
    Compute speed based on target angle and look-ahead distance.
    
    Parameters:
    - convoluted_lidar: Array of filtered lidar distance readings
    - target_angle: Target steering angle in degrees
    - min_speed: Minimum allowed speed (m/s)
    - max_speed: Maximum allowed speed (m/s)
    - look_ahead_width: Width of the forward-looking cone in degrees (±degrees)
    - distance_influence: How much the distance affects speed (0-1)
    - max_safe_distance: Distance at which full speed is allowed (meters)
    - min_safe_distance: Distance at which minimum speed is applied (meters)
    
    Returns:
    - speed: Computed speed value
    """
    angle_magnitude = abs(target_angle)
    
    # Calculate angle-based speed (exponential decay)
    angle_decay_factor = 0.03
    angle_based_speed = max_speed * np.exp(-angle_decay_factor * angle_magnitude)
    
    # Get forward-looking distances (centered around 0 degrees)
    # Assuming convoluted_lidar is indexed by angle
    center_idx = len(convoluted_lidar) // 2  # Assuming center is at the middle of array
    look_ahead_indices = range(center_idx - look_ahead_width, center_idx + look_ahead_width + 1)
    
    # Calculate the minimum distance in the look-ahead cone
    # This protects against out-of-bounds indices
    valid_indices = [i for i in look_ahead_indices if 0 <= i < len(convoluted_lidar)]
    look_ahead_distances = [convoluted_lidar[i] for i in valid_indices]
    min_distance = min(look_ahead_distances) if look_ahead_distances else max_safe_distance
    
    # Calculate distance-based speed factor (linear between min and max safe distances)
    distance_factor = (min_distance - min_safe_distance) / (max_safe_distance - min_safe_distance)
    distance_factor = max(0.0, min(1.0, distance_factor))  # Clamp between 0 and 1
    
    # Calculate distance-based speed
    distance_based_speed = min_speed + distance_factor * (max_speed - min_speed)
    
    # Combine angle-based and distance-based speeds using the influence parameter
    # When distance_influence=0, only angle matters
    # When distance_influence=1, only distance matters
    combined_speed = (1 - distance_influence) * angle_based_speed + distance_influence * distance_based_speed
    
    # Ensure speed stays within bounds
    speed = max(min_speed, min(combined_speed, max_speed))
    
    return speed