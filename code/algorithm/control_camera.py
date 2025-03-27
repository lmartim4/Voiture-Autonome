import time
import numpy as np
from algorithm.interfaces import CameraInterface, SteerInterface, MotorInterface, UltrasonicInterface

def check_reversed_camera(camera: CameraInterface) -> bool:
    """
      Checks if the trolley is upside down (turned 180° in relation to the track)
    using the camera data.

    The function calls camera.process_stream() to get:
      - avg_r: average position of the red pixels (left wall in normal orientation)
      - avg_g: average position of green pixels (right wall in normal orientation)

    In a normal orientation, avg_r < avg_g is expected. If avg_r > avg_g,
    the image shows that the red wall is on the right and the green wall is on the left,
    i.e. the trolley is upside down.

    Args:
        camera (Camera): Instance of the Camera class.

    Returns:
        bool: True if the trolley is upside down, False otherwise.

    """
    avg_r, avg_g, count_r, count_g = camera.process_stream()
    print(f"Avg_r: {avg_r} Avg_g: {avg_g}")
    
    if avg_r < 0 or avg_g < 0:
        return False
    
    return avg_r < avg_g


def reversing_direction(steer: SteerInterface, motor: MotorInterface, back_sensor: UltrasonicInterface, raw_lidar):
    """
    Performs a demi-tour (U-turn) by analyzing LiDAR data to determine the best rotation direction
    and ensuring there are no obstacles in the path.
    
    Args:
        steer: Steering interface to control the car's direction
        motor: Motor interface to control the car's speed
        back_sensor: Ultrasonic sensor interface to get rear distance data
        raw_lidar: LiDAR data array with 360 distance measurements
        
    Returns:
        bool: True if demi-tour was completed successfully, False otherwise
    """
    # Define safety thresholds
    MIN_SAFE_DISTANCE = 20  # cm
    MIN_TURNING_SPACE = 30  # cm
    
    # Analyzing LiDAR data to find the best rotation direction
    front_lidar = raw_lidar[355:5]  # Front region (350° to 10°)
    l_side = raw_lidar[60:120]       # Left side region of the car
    r_side = raw_lidar[240:300]      # Right side region of the car
    
    # Calculate average distances, ignoring zero values
    front_distance = np.mean(front_lidar[front_lidar > 0]) if np.any(front_lidar > 0) else 0
    avg_left = np.mean(l_side[l_side > 0]) if np.any(l_side > 0) else 0
    avg_right = np.mean(r_side[r_side > 0]) if np.any(r_side > 0) else 0
    
    # Get ultrasonic sensor data for rear distance
    back_distance = back_sensor.get_ultrasonic_data()
    print(f"LiDAR - Front: {front_distance:.1f}cm, Left: {avg_left:.1f}cm, Right: {avg_right:.1f}cm")
    print(f"Ultrasonic back distance: {back_distance:.1f}cm")
    
    # Check if there's enough space for the maneuver
    if back_distance < MIN_SAFE_DISTANCE:
        print("Not enough space behind for demi-tour, aborting...")
        return False
    
    # Check if there's a wall or obstacle too close in front
    if front_distance < MIN_SAFE_DISTANCE:
        print("Obstacle too close in front, proceeding with caution...")
    
    # Check if there's enough space on either side for turning
    if max(avg_left, avg_right) < MIN_TURNING_SPACE:
        print("Not enough space on either side for a safe demi-tour, aborting...")
        return False
    
    # Determine which side has more space and execute the turn accordingly
    if avg_left > avg_right:
        print("Free space on the left, rotating left...")
        turn_left = True
    else:
        print("Free space on the right, rotating right...")
        turn_left = False
    
    # Execute the turn with continuous safety checks
    try:
        # Phase 1: Reverse with appropriate steering
        steer_angle = +20 if turn_left else -20
        steer.set_steering_angle(steer_angle)
        motor.set_speed(-1.5)  # Start slower for safety
        
        # Safety check during reverse phase
        start_time = time.time()
        while time.time() - start_time < 1.5:
            back_distance = back_sensor.get_ultrasonic_data()
            if back_distance < MIN_SAFE_DISTANCE / 2:  # Getting dangerously close
                print("Warning: Obstacle detected behind, adjusting...")
                motor.set_speed(-0.5)  # Slow down
            time.sleep(0.1)  # Check every 100ms
        
        # Phase 2: Stop momentarily
        motor.set_speed(0)
        time.sleep(0.5)
        
        # Phase 3: Forward with opposite steering to complete the turn
        steer.set_steering_angle(-steer_angle)
        motor.set_speed(1.2)  # Slightly slower for controlled turning
        
        # Safety check during forward phase
        start_time = time.time()
        while time.time() - start_time < 1.5:
            # Quick LiDAR scan of front area
            front_scan = raw_lidar[350:10]
            front_min = np.min(front_scan[front_scan > 0]) if np.any(front_scan > 0) else float('inf')
            
            if front_min < MIN_SAFE_DISTANCE:
                print("Warning: Obstacle detected ahead, adjusting...")
                motor.set_speed(0.5)  # Slow down
            time.sleep(0.1)  # Check every 100ms
        
        # Phase 4: Straighten wheels and normalize speed
        steer.set_steering_angle(0)
        motor.set_speed(1.0)
    except Exception as e:
        # Emergency stop if any error occurs
        print(f"Error during demi-tour: {e}")
        motor.set_speed(0)
        steer.set_steering_angle(0)
        return False
    
    print("Demi-tour completed")
    return True