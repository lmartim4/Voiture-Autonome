from algorithm.constants import *
import numpy as np

def compute_speed2(convoluted_lidar, target_angle: float, 
                  min_speed=0.4, max_speed=1.6, 
                  look_ahead_width=5, distance_influence=0.5,
                  max_safe_distance=2.0, min_safe_distance=0.4):
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
    if (look_ahead_distances != 0):
        min_distance = min(look_ahead_distances) 
    else:
        min_distance = max_safe_distance
    
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
    print(f"Min Dist:{min_distance}")
    if (min_distance < 0.5):
        speed = 0.0
    else:    
        speed = max(min_speed, min(combined_speed, max_speed))

    return speed

def compute_speed(convoluted_lidar, target_angle: float):
    MIN_SPEED = 0.5  # Minimum speed for curves
    MAX_SPEED = 1.0 # Maximum speed for straight paths
    STOP_DISTANCE = 0.30  # Distance in cm to stop completely
    SLOW_DISTANCE = 0.80  # Distance in cm to start slowing down
    
    # Check frontal distance from LiDAR
    # Assuming front is around indices 350-359 and 0-10
    front_indices = list(range(350, 360)) + list(range(0, 11))
    front_data = [convoluted_lidar[i] for i in front_indices if convoluted_lidar[i] > 0]
    
    # Calculate the average frontal distance if we have valid readings
    if len(front_data) > 0:
        front_distance = sum(front_data) / len(front_data)
    else:
        front_distance = float('inf')  # No valid readings means no obstacles detected
    
    # First calculate speed based on angle
    angle_magnitude = abs(target_angle)
    decay_factor = 0.03
    
    speed = MAX_SPEED * np.exp(-decay_factor * angle_magnitude)
    speed = max(speed, MIN_SPEED)
    speed = min(speed, MAX_SPEED)
    
    # Then adjust speed based on frontal distance
    if front_distance <= STOP_DISTANCE:
        # Too close to wall, stop completely
        print(f"Front distance = {front_distance}")
        return 0.0
    elif front_distance < SLOW_DISTANCE:
        # Gradually slow down as we approach obstacles
        # Linear scaling between full calculated speed and zero
        distance_factor = (front_distance - STOP_DISTANCE) / (SLOW_DISTANCE - STOP_DISTANCE)
        speed *= distance_factor
    
    return speed