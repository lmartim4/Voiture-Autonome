import time
import numpy as np
from scipy.signal import convolve
from typing import Any, Dict, Tuple
from constants import *

last_reverse = None
reverse_counter = 0

def stop_command() -> Tuple[float, float]:
    """
    Returns commands to stop both actuators.

    Returns:
        Tuple[float, float]: commands to stop both actuators.
    """
    return STEER2PWM_B, SPEED2DC_B

def transform_back(filtered: np.ndarray) -> np.ndarray:
    """
    Transforms the filtered FOV data back into a full 360° array.
    The filtered values are inserted into their original angular positions,
    while the angles outside the FOV are filled with 0.0 (or another placeholder).

    Args:
        filtered (np.ndarray): Filtered lidar data for the FOV (length = FIELD_OF_VIEW).

    Returns:
        np.ndarray: Full 360-element lidar data array.
    """
    # Create a full-length array filled with 0.0.
    full = np.zeros(360, dtype=filtered.dtype)

    # Compute the original shift that was applied.
    shift = -LIDAR_HEADING_OFFSET_DEG + FIELD_OF_VIEW_DEG // 2
    # To reverse the roll, determine where the FOV data should go.
    start_idx = (-shift) % 360
    end_idx = (start_idx + FIELD_OF_VIEW_DEG) % 360

    if start_idx < end_idx:
        full[start_idx:end_idx] = filtered
    else:
        # Handle wrap-around at the 360° boundary.
        num_to_end = 360 - start_idx
        full[start_idx:] = filtered[:num_to_end]
        full[:end_idx] = filtered[num_to_end:]

    return full

def filter(distances: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Filters the lidar points that are in the vehicle's field
    of view and smoothes the measurement using convolution.

    Args:
        distances (np.ndarray): lidar measurements in meters.

    Returns:
        Tuple[np.ndarray, np.ndarray]: filtered and smoothed lidar
        measurements along with the respective ray angles in degrees.
    """

    shift = -LIDAR_HEADING_OFFSET_DEG + FIELD_OF_VIEW_DEG // 2

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

def compute_steer(data: Dict[str, Any]) -> Tuple[float, float]:
    """
    Computes the steering angle and duty cycle based on lidar data.

    Args:
        data (Dict[str, Any]): dictionary containing lidar and serial data.

    Returns:
        Tuple[float, float]: computed steering angle and respective duty cycle.
    """

    distances, angles = filter(data["lidar"])

    angle = angles[np.argmax(distances)]

    l_angle = AVOID_CORNER_MAX_ANGLE
    r_angle = AVOID_CORNER_MAX_ANGLE

    for index in range(1, 8):
        l_dist = data["lidar"][(angle + index) % 360]
        r_dist = data["lidar"][(angle - index) % 360]

        if l_angle == 8 and l_dist < AVOID_CORNER_MIN_DISTANCE:
            l_angle = index
            #print(f"l_dist: {l_dist}")

        if r_angle == 8 and r_dist < AVOID_CORNER_MIN_DISTANCE:
            r_angle = index
            #print(f"r_dist: {r_dist}")

    if l_angle > r_angle:
        delta = -AVOID_CORNER_SCALE_FACTOR * (AVOID_CORNER_MAX_ANGLE - r_angle)
    else:
        delta =  AVOID_CORNER_SCALE_FACTOR * (AVOID_CORNER_MAX_ANGLE - l_angle)

    #print(delta, l_angle, r_angle)
    alpha = angle - LIDAR_HEADING_OFFSET_DEG - delta

    steer = np.sign(alpha) * lerp(np.abs(alpha), STEER_FACTOR)
    pwm = steer * STEER2PWM_A + STEER2PWM_B

    return steer, pwm

def compute_speed(data: Dict[str, Any], steer: float) -> Tuple[float, float]:
    """
    Computes the speed and duty cycle based on lidar data and steering angle.

    Args:
        data (Dict[str, Any]): dictionary containing lidar and serial data.
        steer (float): computed steering angle in degrees.

    Returns:
        Tuple[float, float]: computed speed and respective duty cycle.
    """

    shift = int(-LIDAR_HEADING_OFFSET_DEG + APERTURE_ANGLE // 2)
    
    dfront = np.mean(np.roll(data["lidar"], shift)[:APERTURE_ANGLE])

    speed = (1.0 - AGGRESSIVENESS) * lerp(dfront, SPEED_FACTOR_DIST)
    speed = AGGRESSIVENESS + speed * lerp(np.abs(steer), SPEED_FACTOR_ANG)

    duty_cycle = speed * SPEED2DC_A + SPEED2DC_B

    return speed, duty_cycle

def get_nonzero_points_in_hitbox(lidar):
    """
    Returns only the nonzero LiDAR points inside the defined hitbox.
    
    Args:
        lidar (np.array): Array containing lidar distance readings (360 values).
        
    Returns:
        Tuple[np.ndarray, np.ndarray]: Arrays of x and y coordinates inside the hitbox (nonzero only).
    """

    # Filter valid lidar points
    mask = (0 < lidar) & (lidar < 360)
    distances = lidar[mask]
    angles = np.deg2rad(np.arange(0, 360)[mask])

    # Convert polar to Cartesian coordinates
    x = distances * np.cos(angles)
    y = distances * np.sin(angles)

    # Define hitbox conditions
    mask_hitbox = (np.abs(y) <= HITBOX_WIDTH) & (np.abs(x) <= HITBOX_HEIGHT) & (y * x != 0)

    return x[mask_hitbox], y[mask_hitbox]


def check_reverse(distances) -> bool:
    hitsx, hitsy = get_nonzero_points_in_hitbox(distances)
    # Use np.count_nonzero to count the nonzero elements.
    if np.count_nonzero(hitsx) > MIN_POINTS_TO_TRIGGER:
        return True
    return False

def reverse(interface: Dict[str, Any], data: Dict[str, Any]) -> None:
    """
    Executes the reverse maneuver based on interface and lidar data.

    Args:
        interface (Dict[str, Any]): dictionary containing interface components.
        data (Dict[str, Any]): dictionary containing lidar and serial data.
    """

    global last_reverse
    
    interface["lidar"].stop()

    #Setting ESC in reverse mode
    interface["speed"].set_duty_cycle(7.0)
    time.sleep(0.03)
    interface["speed"].set_duty_cycle(7.5)
    time.sleep(0.03)
    #end of setting ESC in reverse mode

    for _ in range(20):
        serial = interface["serial"].read(depth=5)

        if 30.0 <= serial[1]:
            break

        time.sleep(0.1)

    distances = data["lidar"]
    indices = np.arange(-5, 6, dtype=int) + 70

    r_side = np.mean(distances[(LIDAR_HEADING_OFFSET_DEG - indices) % 360])
    l_side = np.mean(distances[(LIDAR_HEADING_OFFSET_DEG + indices) % 360])

    steer = STEERING_LIMIT_IN_REVERSE if r_side > l_side else -STEERING_LIMIT_IN_REVERSE

    interface["steer"].set_duty_cycle(0.7*steer * STEER2PWM_A + STEER2PWM_B)
    interface["speed"].set_duty_cycle(PWM_REVERSE)

    interface["lidar"].start()
    
    for _ in range(10):
        if serial[1] < 20.0:
            break

        time.sleep(0.1)

    interface["speed"].set_duty_cycle(7.5)
    
    last_reverse = time.time()

