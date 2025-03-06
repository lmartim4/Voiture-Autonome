import time
from console import Console
import numpy as np
from scipy.signal import convolve
from typing import Any, Dict, Tuple
from constants import *
from camera import Camera  # Importe a classe Camera do módulo camera

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
            print(f"l_dist: {l_dist}")

        if r_angle == 8 and r_dist < 2.5:
            r_angle = index
            print(f"r_dist: {r_dist}")

    if l_angle > r_angle:
        delta = -1.2 * (8 - r_angle)
    else:
        delta = 1.2 * (8 - l_angle)

    print(delta, l_angle, r_angle)
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

def check_reversed_camera(camera: Camera) -> bool:
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
    
    # Se algum dos valores não for detectado (ex: -1), não há informação suficiente.
    if avg_r < 0 or avg_g < 0:
        return False
    
    # Em orientação normal, avg_r deve ser menor que avg_g.
    return avg_g > avg_r

def reversing_direction(interface: Dict[str, Any], data: Dict[str, Any]) -> None:

    # Analisando os dados do LiDAR para encontrar a melhor direção de rotação
    distances = data["lidar"]
    l_side = distances[60:120]   # Região à esquerda do carrinho
    r_side = distances[240:300]  # Região à direita do carrinho
                
    avg_left = np.mean(l_side[l_side > 0])
    avg_right = np.mean(r_side[r_side > 0])
                
    if avg_left > avg_right:
        console.info("Espace libre à gauche, rotation vers la gauche...")
        correction_steer_pwm = STEER2PWM_B + (STEERING_LIMIT * STEER2PWM_A)
    else:
        console.info("Espace libre à droite, rotation vers la droite...")
        correction_steer_pwm = STEER2PWM_B - (STEERING_LIMIT * STEER2PWM_A)

    # Aplicando os ajustes de direção
    interface["steer"].set_duty_cycle(correction_steer_pwm)

    # Reduzindo a velocidade para uma correção segura
    interface["speed"].set_duty_cycle(PWM_REVERSE)

    # Pequena pausa para a correção
    time.sleep(0.5)

    # Após a correção, recalculamos o steer e speed
    steer, steer_pwm = compute_steer(data)
    speed, speed_pwm = compute_speed(data, steer)

    # Aplicar os novos valores após a correção
    interface["steer"].set_duty_cycle(steer_pwm)
    interface["speed"].set_duty_cycle(speed_pwm)


def reverse_with_camera(interface: Dict[str, Any], camera: Camera) -> None:
    """
    Performs the reverse maneuver based on the camera data.

    The idea is that the red dots (left wall) and green dots (right wall)
    indicate the space available. If the space is small, the reverse should be slower and,
    if one side is freer than the other, the trolley's direction will be adjusted.

    Args:
        interface (Dict[str, Any]): Dictionary containing the trolley's components.
        camera (Camera): Camera instance for analyzing the environment.
    """
    global last_reverse

    interface["lidar"].stop()  # Para leituras inconsistentes do LiDAR durante a manobra

    console.info("Manœuvre de recul basée sur la caméra...")
    
    avg_r, avg_g, count_r, count_g = camera.process_stream()

    # If there isn't enough information, make a cautious U-turn
    if avg_r < 0 or avg_g < 0:
        console.info("Ré prudent - peu d'informations de la part de la caméra")
        steer_pwm = STEER2PWM_B  # Neutral direction
        speed_pwm = PWM_REVERSE * 0.7  # Slower reverse
    else:
        # Calculate space between detected walls
        gap = avg_g - avg_r

        # If the space is too small, reduce the speed
        if gap < 100:  
            console.info("Espace restreint - marche arrière plus lente")
            speed_pwm = PWM_REVERSE * 0.6  # Slow reverse
        else:
            speed_pwm = PWM_REVERSE  # Normal reverse

        # Decide on direction based on available space
        if avg_r > avg_g:
            console.info("Espace plus grand à gauche - tourner à gauche en marche arrière")
            steer_pwm = STEER2PWM_B + (STEERING_LIMIT * STEER2PWM_A)  
        else:
            console.info("Espace plus grand à droite - tourner à droite en marche arrière")
            steer_pwm = STEER2PWM_B - (STEERING_LIMIT * STEER2PWM_A) 
        
        speed_pwm = PWM_REVERSE  # Normal speed for reverse

    # Small speed adjustments to avoid jerks
    interface["speed"].set_duty_cycle(7.0)
    time.sleep(0.03)
    interface["speed"].set_duty_cycle(7.5)
    time.sleep(0.03)

    # Perform the reverse maneuver for a short time to avoid long adjustments
    interface["steer"].set_duty_cycle(steer_pwm)
    interface["speed"].set_duty_cycle(speed_pwm)

    time.sleep(1.0)  # Time setting for the maneuver

    # Returns to normal control
    interface["speed"].set_duty_cycle(7.5)  # Stop the reverse movement
    interface["lidar"].start()  # Reactivate LiDAR for new readings

    last_reverse = time.time()
    console.info("Ré terminée, retour au contrôle normal")
