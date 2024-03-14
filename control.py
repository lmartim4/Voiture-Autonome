import numpy as np

from scipy.signal import convolve

from typing import Any, Dict, List, Tuple

from constants import *


def filter(distances: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Filters a circular sector (field of view) of the point cloud.

    Args:
        distances (np.ndarray): vector with distances ordered by angle.

    Returns:
        Tuple[np.ndarray, np.ndarray]: tuple containing the
            vector with distances and the vector with angles,
            both filtered for the field of view of interest.
    """

    shift = -LIDAR_HEADING + FIELD_OF_VIEW // 2

    angles = np.arange(0, 360)
    angles = np.roll(angles, shift)

    distances = np.roll(distances, shift)

    kernel = np.ones(CONVOLUTION_SIZE) / CONVOLUTION_SIZE
    distances = convolve(distances, kernel, mode="same")

    return distances[:FIELD_OF_VIEW], angles[:FIELD_OF_VIEW]


def lerp(value: float, factor: np.ndarray) -> np.ndarray:
    indices = np.nonzero(value < factor[:, 0])[0]

    if len(indices) == 0:
        return factor[-1, 1]

    index = indices[0]

    delta = factor[index] - factor[index - 1]
    scale = (value - factor[index - 1, 0]) / delta[0]

    return factor[index - 1, 1] + scale * delta[1]


def compute_steer(data: Dict[str, Any]) -> Tuple[float, float]:
    distances, angles = filter(data["lidar"])

    angle = angles[np.argmax(distances)]

    angle_upper =  5
    angle_lower = -5

    for index in range(1, 6):
        if data["lidar"][angle + index] < 0.5:
            angle_upper = index

        if data["lidar"][angle - index] < 0.5:
            angle_lower = -index

    delta = angle_upper + angle_lower
    alpha = angle - LIDAR_HEADING + delta

    steer = np.sign(alpha) * lerp(np.abs(alpha), STEER_FACTOR)
    pwm = steer * STEER2PWM_A + STEER2PWM_B

    return steer, pwm


def compute_speed(data: Dict[str, Any]) -> Tuple[float, float]:
    aperture_angle = 20

    shift = -LIDAR_HEADING + aperture_angle // 2

    dfront = np.mean(np.roll(data["lidar"], shift)[:aperture_angle])
    speed = np.clip(0.5 + 0.5 * lerp(dfront, SPEED_FACTOR), 0.0, 1.0)

    if dfront < 0.2:
        speed = 0.0

    pwm = speed * SPEED2PWM_A + SPEED2PWM_B

    return speed, pwm


def stop_command() -> Tuple[float, float]:
    return STEER2PWM_B, SPEED2PWM_B
