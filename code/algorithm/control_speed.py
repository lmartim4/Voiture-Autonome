from algorithm.constants import *
import numpy as np

def compute_speed(convoluted_lidar, target_angle: float):
    MIN_SPEED = 0.5  # Minimum speed for curves
    MAX_SPEED = 1.1  # Maximum speed for straight paths
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
        return 0.0
    elif front_distance < SLOW_DISTANCE:
        # Gradually slow down as we approach obstacles
        # Linear scaling between full calculated speed and zero
        distance_factor = (front_distance - STOP_DISTANCE) / (SLOW_DISTANCE - STOP_DISTANCE)
        speed *= distance_factor
    
    return speed