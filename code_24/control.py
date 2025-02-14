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
    return STEER2PWM_B, SPEED2PWM_B

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

    shift = -LIDAR_HEADING + FIELD_OF_VIEW // 2

    angles = np.arange(0, 360)
    angles = np.roll(angles, shift)

    distances = np.roll(distances, shift)

    kernel = np.ones(CONVOLUTION_SIZE) / CONVOLUTION_SIZE
    distances = convolve(distances, kernel, mode="same")

    return distances[:FIELD_OF_VIEW], angles[:FIELD_OF_VIEW]


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

    l_angle = 8
    r_angle = 8

    for index in range(1, 8):
        l_dist = data["lidar"][(angle + index) % 360]
        r_dist = data["lidar"][(angle - index) % 360]

        if l_angle == 8 and l_dist < 2.5:
            l_angle = index
            #print(f"l_dist: {l_dist}")

        if r_angle == 8 and r_dist < 2.5:
            r_angle = index
            #print(f"r_dist: {r_dist}")

    if l_angle > r_angle:
        delta = -1.2 * (8 - r_angle)
    else:
        delta = 1.2 * (8 - l_angle)

    #print(delta, l_angle, r_angle)
    alpha = angle - LIDAR_HEADING - delta

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
    aperture_angle = 20

    shift = -LIDAR_HEADING + aperture_angle // 2

    dfront = np.mean(np.roll(data["lidar"], shift)[:aperture_angle])

    speed = 0.7 * lerp(dfront, SPEED_FACTOR_DIST)
    speed = 0.3 + speed * lerp(np.abs(steer), SPEED_FACTOR_ANG)

    pwm = speed * SPEED2PWM_A + SPEED2PWM_B

    return speed, pwm


def check_reverse(data: Dict[str, Any]) -> bool:
    """
    Checks if the vehicle should reverse based on lidar and serial data.

    Args:
        data (Dict[str, Any]): dictionary containing lidar and serial data.

    Returns:
        bool: True if the vehicle should reverse, False otherwise.
    """

    global last_reverse, reverse_counter

    now = time.time()

    if last_reverse is None:
        last_reverse = now

    if data["serial"][0] == 0.0 and now - last_reverse > 2.0:
        last_reverse = now

        return True

    HEIGHT = lerp(data["serial"][0], HEIGHT_FACTOR)
    MAX_DIST = np.sqrt(0.25 * WIDTH**2 + HEIGHT**2)

    mask = (0 < data["lidar"]) & (data["lidar"] < MAX_DIST)

    distances = data["lidar"][mask]
    angles = np.deg2rad(np.arange(0, 360)[mask] - LIDAR_HEADING)

    x = distances * np.cos(angles)
    y = distances * np.sin(angles)

    mask = (np.abs(y) <= 0.5 * WIDTH) & (0.0 <= x) & (x <= HEIGHT)

    if np.count_nonzero(mask) > 8:
        reverse_counter += 1

    else:
        reverse_counter = 0

    if reverse_counter > 8:
        reverse_counter = 0

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

    interface["speed"].set_duty_cycle(7.0)
    time.sleep(0.03)
    interface["speed"].set_duty_cycle(7.5)
    time.sleep(0.03)

    for attempt in range(20):
        serial = interface["serial"].read(depth=5)

        if 30.0 <= serial[1]:
            break

        time.sleep(0.1)

    distances = data["lidar"]
    indices = np.arange(-5, 6, dtype=int) + 70

    r_side = np.mean(distances[(LIDAR_HEADING - indices) % 360])
    l_side = np.mean(distances[(LIDAR_HEADING + indices) % 360])

    steer = STEERING_LIMIT if r_side > l_side else -STEERING_LIMIT

    interface["steer"].set_duty_cycle(0.7*steer * STEER2PWM_A + STEER2PWM_B)
    interface["speed"].set_duty_cycle(PWM_REVERSE)

    interface["lidar"].start()
    
    for attempt in range(10):
        if serial[1] < 20.0:
            break

        time.sleep(0.1)

    interface["speed"].set_duty_cycle(7.5)

    last_reverse = time.time()

