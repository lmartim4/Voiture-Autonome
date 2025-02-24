import time
import numpy as np
from scipy.signal import convolve
from typing import Any, Dict, Tuple
from constants import *

reverse_running = False
reverse_counter = 0

def stop_command() -> Tuple[float, float]:
    """
    Returns commands to stop both actuators.

    Returns:
        Tuple[float, float]: commands to stop both actuators.
    """
    return STEER_CENTER, SPEED2DC_B

def convolution_filter(distances: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Filters the lidar points that are in the vehicle's field
    of view and smoothes the measurement using convolution.

    Args:
        distances (np.ndarray): lidar measurements in meters.

    Returns:
        Tuple[np.ndarray, np.ndarray]: filtered and smoothed lidar
        measurements along with the respective ray angles in degrees.
    """

    shift = FIELD_OF_VIEW_DEG // 2

    angles = np.arange(0, 360)
    angles = np.roll(angles, shift)

    distances = np.roll(distances, shift)

    kernel = np.ones(CONVOLUTION_SIZE) / CONVOLUTION_SIZE
    distances = convolve(distances, kernel, mode="same")

    return distances[:FIELD_OF_VIEW_DEG], angles[:FIELD_OF_VIEW_DEG]

def lerp(value: float, factor: np.ndarray) -> np.ndarray:
    """
    Linearly interpolates a value based on a given interpolation map.

    Args:
        value (float): value to be interpolated.
        lerp_map (np.ndarray): array containing the interpolation map.

    Returns:
        np.ndarray: interpolated value.
    """

    indices = np.nonzero(value < factor[:, 0])[0]

    if len(indices) == 0:
        return factor[-1, 1]

    index = indices[0]

    delta = factor[index] - factor[index - 1]
    scale = (value - factor[index - 1, 0]) / delta[0]

    return factor[index - 1, 1] + scale * delta[1]

def compute_target(lidar_readings):
    distances, angles = convolution_filter(lidar_readings)
    target_angle = angles[np.argmax(distances)]

    target_angle = (target_angle + 180) % 360 - 180

    #print(f"Compute alpha found {target_angle}")
    return target_angle

def compute_steer(alpha):
    return np.sign(alpha) * lerp(np.abs(alpha), STEER_FACTOR)

def compute_pwm(steer):
    return steer * STEER_VARIATION_RATE + STEER_CENTER

def compute_steer_from_lidar(lidar_readings) -> Tuple[float, float, int]:
    """
    Computes the steering angle and duty cycle based on lidar data.

    Args:
        data (Dict[str, Any]): dictionary containing lidar and serial data.

    Returns:
        Tuple[float, float]: computed steering angle and respective duty cycle.
    """
    
    
    # l_angle = AVOID_CORNER_MAX_ANGLE
    # r_angle = AVOID_CORNER_MAX_ANGLE

    # for index in range(1, 8):
    #     l_dist = lidar_readings[(target_angle + index) % 360]
    #     r_dist = lidar_readings[(target_angle - index) % 360]

    #     if l_angle == 8 and l_dist < AVOID_CORNER_MIN_DISTANCE:
    #         l_angle = index
    #         #print(f"l_dist: {l_dist}")

    #     if r_angle == 8 and r_dist < AVOID_CORNER_MIN_DISTANCE:
    #         r_angle = index
    #         #print(f"r_dist: {r_dist}")

    # if l_angle > r_angle:
    #     delta = -AVOID_CORNER_SCALE_FACTOR * (AVOID_CORNER_MAX_ANGLE - r_angle)
    # else:
    #     delta =  AVOID_CORNER_SCALE_FACTOR * (AVOID_CORNER_MAX_ANGLE - l_angle)

    #print(delta, l_angle, r_angle)

    target = compute_target(lidar_readings)
    steer = compute_steer(target)
    pwm = compute_pwm(steer)

    return steer, pwm, target

def compute_speed(distances, steer: float) -> Tuple[float, float]:
    """
    Computes the speed and duty cycle based on lidar data and steering angle.

    Args:
        data (Dict[str, Any]): dictionary containing lidar and serial data.
        steer (float): computed steering angle in degrees.

    Returns:
        Tuple[float, float]: computed speed and respective duty cycle.
    """

    shift = int(APERTURE_ANGLE // 2)
    
    dfront = np.mean(np.roll(distances, shift)[:APERTURE_ANGLE])

    speed = (1.0 - AGGRESSIVENESS) * lerp(dfront, SPEED_FACTOR_DIST)
    speed = AGGRESSIVENESS + speed * lerp(np.abs(steer), SPEED_FACTOR_ANG)

    duty_cycle = speed * SPEED2DC_A + SPEED2DC_B
    
    return speed, duty_cycle

def check_reverse(distances) -> bool:
    hitx, hity = get_nonzero_points_in_hitbox(distances)
    
    if(hitx.size > MIN_POINTS_TO_TRIGGER or hity.size > MIN_POINTS_TO_TRIGGER):
        return True
    
    return False

def set_esc_on_reverse(speed_interface):
    speed_interface.set_duty_cycle(7.0)
    time.sleep(0.03)
    speed_interface.set_duty_cycle(7.5)
    time.sleep(0.03)
    
def activate_reverse(speed_interface):
    set_esc_on_reverse(speed_interface)
    speed_interface.set_duty_cycle(PWM_REVERSE)

def deactivate_reverse(speed_interface):
    speed_interface.set_duty_cycle(DC_SPEED_MIN)
    
def reverse(interface: Dict[str, Any], data: Dict[str, Any]) -> None:
    """
    Executes the reverse maneuver based on interface and lidar data.

    Args:
        interface (Dict[str, Any]): dictionary containing interface components.
        data (Dict[str, Any]): dictionary containing lidar and serial data.
    """
    global reverse_running

    if(reverse_running):
        print("Reverse already running")
        return
    
    reverse_running = True
    set_esc_on_reverse(interface["speed"])

    distances = data["lidar"]
    indices = np.arange(-5, 6, dtype=int) + 70

    r_side = np.mean(distances[(-indices) % 360])
    l_side = np.mean(distances[(+indices) % 360])

    steer = STEERING_LIMIT_IN_REVERSE if r_side > l_side else -STEERING_LIMIT_IN_REVERSE

    interface["steer"].set_duty_cycle(0.7*steer * STEER_VARIATION_RATE + STEER_CENTER)
    interface["speed"].set_duty_cycle(PWM_REVERSE)

    #interface["lidar"].start()
    

    reverse_running = False

    for _ in range(10):
        # if serial[1] < 20.0:
        #     break

        time.sleep(0.1)

    interface["speed"].set_duty_cycle(7.5)

def get_nonzero_points_in_hitbox(distances):
    """
    Returns only the nonzero LiDAR points inside the defined hitbox.
    
    Args:
        lidar (np.array): Array containing lidar distance readings (360 values).
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: Arrays of x and y coordinates inside the hitbox (nonzero only).
    """
    if distances is None:
        raise ValueError("Error: LiDAR input is None.")

    angles = np.deg2rad(np.arange(0, 360))

    # Convert polar to Cartesian coordinates
    x = distances * np.cos(angles)
    y = -distances * np.sin(angles)

    # Define hitbox conditions
    mask_hitbox = (np.abs(y) <= HITBOX_WIDTH) & (np.abs(x) <= HITBOX_HEIGHT) & (y * x != 0.0)

    return x[mask_hitbox], y[mask_hitbox]