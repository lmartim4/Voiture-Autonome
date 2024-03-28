import time

import numpy as np

from scipy.signal import convolve

from typing import Any, Dict, Tuple

from constants import *


last_reverse = None

reverse_counter = 0


def stop_command() -> Tuple[float, float]:
    return STEER2PWM_B, SPEED2PWM_B


def filter(distances: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
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
        if data["lidar"][(angle + index) % 360] < 0.5:
            angle_upper = index

        if data["lidar"][(angle - index) % 360] < 0.5:
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

    speed = np.clip(0.65 + 0.35 * lerp(dfront, SPEED_FACTOR), 0.0, 1.0)
    pwm = speed * SPEED2PWM_A + SPEED2PWM_B

    return speed, pwm


def check_reverse(data: Dict[str, Any]) -> bool:
    global last_reverse, reverse_counter

    now = time.time()

    if last_reverse is None:
        last_reverse = now

    if data["serial"][0] == 0.0 and now - last_reverse > 2.0:
        last_reverse = now

        return True

    HEIGHT = lerp(data["serial"][0], HEIGHT_FACTOR)
    MAX_DIST = np.sqrt(0.25 * WIDTH**2 + HEIGHT**2)

    mask = data["updated"] & (data["lidar"] < MAX_DIST)

    distances = data["lidar"][mask]
    angles = np.deg2rad(np.arange(0, 360)[mask] - LIDAR_HEADING)

    x = distances * np.cos(angles)
    y = distances * np.sin(angles)

    mask = (np.abs(y) <= 0.5 * WIDTH) & (0.0 <= x) & (x <= HEIGHT)

    if np.count_nonzero(mask) > 5:
        reverse_counter += 1

    else:
        reverse_counter = 0

    if reverse_counter > 3:
        reverse_counter = 0

        return True

    return False


def reverse(interface: Dict[str, Any], data: Dict[str, Any]) -> None:
    interface["lidar"].stop()

    interface["speed"].set_duty_cycle(7.0)
    time.sleep(0.03)
    interface["speed"].set_duty_cycle(7.5)
    time.sleep(0.03)

    for attempt in range(5):
        serial = interface["serial"].read(depth=5)

        if 20.0 <= serial[1]:
            break

        time.sleep(0.5)

    distances = data["lidar"]
    indices = np.arange(-5, 6, dtype=int) + 70

    r_side = np.mean(distances[(LIDAR_HEADING - indices) % 360])
    l_side = np.mean(distances[(LIDAR_HEADING + indices) % 360])

    steer = STEERING_LIMIT if r_side > l_side else -STEERING_LIMIT

    interface["steer"].set_duty_cycle(steer * STEER2PWM_A + STEER2PWM_B)
    interface["speed"].set_duty_cycle(PWM_REVERSE)

    time.sleep(0.5)
    interface["lidar"].start()
    time.sleep(1.0)

    interface["speed"].set_duty_cycle(7.5)
