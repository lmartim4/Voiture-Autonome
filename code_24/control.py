import time
import numpy as np
from scipy.signal import convolve
from typing import Any, Dict, Tuple
from constants import *

reverse_running = False
reverse_counter = 0

def lerp(value: float, factor: np.ndarray) -> np.ndarray:
    indices = np.nonzero(value < factor[:, 0])[0]

    if len(indices) == 0:
        return factor[-1, 1]

    index = indices[0]

    delta = factor[index] - factor[index - 1]
    scale = (value - factor[index - 1, 0]) / delta[0]

    return factor[index - 1, 1] + scale * delta[1]

def stop_command():
    return STEER_CENTER, DC_SPEED_MIN

def convolution_filter(distances: np.ndarray):
    shift = FIELD_OF_VIEW_DEG // 2

    kernel = np.ones(CONVOLUTION_SIZE) / CONVOLUTION_SIZE
        
    angles = np.arange(0, 360)
    angles = np.roll(angles, shift)
    
    distances = np.roll(distances, shift)
    distances = convolve(distances, kernel, mode="same")

    return distances[:FIELD_OF_VIEW_DEG], angles[:FIELD_OF_VIEW_DEG]

def compute_angle(filtred_distances, filtred_angles):
    target_angle = filtred_angles[np.argmax(filtred_distances)]
    target_angle = (target_angle + 180) % 360 - 180
    return target_angle

def compute_steer(alpha):
    return np.sign(alpha) * lerp(np.abs(alpha), STEER_FACTOR)

def compute_pwm(steer):
    return steer * STEER_VARIATION_RATE + STEER_CENTER

def compute_steer_from_lidar(lidar_readings):    
    filtreed_distances, filtreed_angles = convolution_filter(lidar_readings)
    target = compute_angle(filtreed_distances, filtreed_angles)
    steer = compute_steer(target)
    pwm = compute_pwm(steer)

    return steer, pwm, target

def compute_speed(distances, steer: float):
    shift = int(APERTURE_ANGLE // 2)
    
    dfront = np.mean(np.roll(distances, shift)[:APERTURE_ANGLE])

    speed = (1.0 - AGGRESSIVENESS) * lerp(dfront, SPEED_FACTOR_DIST)
    speed = AGGRESSIVENESS + speed * lerp(np.abs(steer), SPEED_FACTOR_ANG)

    duty_cycle = speed * SPEED2DC_A + SPEED2DC_B
    
    return speed, duty_cycle

def check_reverse(distances):
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
    
def reverse(interface: Dict[str, Any], data: Dict[str, Any]):
    global reverse_running

    if(reverse_running):
        print("Reverse already running")
        return
    
    reverse_running = True
    activate_reverse(interface["speed"])

    distances = data["lidar"]
    indices = np.arange(-5, 6, dtype=int) + 70
    
    r_side = np.mean(distances[(-indices) % 360])
    l_side = np.mean(distances[(+indices) % 360])

    steer = STEERING_LIMIT_IN_REVERSE if r_side > l_side else -STEERING_LIMIT_IN_REVERSE

    interface["steer"].set_duty_cycle(0.7*steer * STEER_VARIATION_RATE + STEER_CENTER)
    interface["speed"].set_duty_cycle(PWM_REVERSE)

    reverse_running = False

    for _ in range(20):
        time.sleep(0.1)

    deactivate_reverse(interface["speed"])
    
    interface["speed"].set_duty_cycle(7.5)
    

def get_nonzero_points_in_hitbox(distances):
    if distances is None:
        raise ValueError("Error: LiDAR input is None.")

    x, y = convert_rad_to_xy(distances, np.arange(0, 360))

    mask_hitbox =  (y > 0) & (np.abs(y) <= HITBOX_HEIGHT) & (np.abs(x) <= HITBOX_WIDTH) & (y * x != 0.0)

    return x[mask_hitbox], y[mask_hitbox]

@staticmethod
def convert_rad_to_xy(distance, angle_rad):
    y = distance * np.cos(angle_rad)
    x = distance * np.sin(angle_rad)
    return x, y