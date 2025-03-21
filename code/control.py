import time
import numpy as np
from scipy.signal import convolve
from typing import Any, Dict, Tuple
from algorithm.constants import *
from algorithm.interfaces import CameraInterface

reverse_running = False
reverse_counter = 0

def check_reverse(distances):
    return False
    hitx, hity = get_nonzero_points_in_hitbox(distances)
    
    if(hitx.size > MIN_POINTS_TO_TRIGGER or hity.size > MIN_POINTS_TO_TRIGGER):
        return True
    
    return False

def reverse(interface: Dict[str, Any], raw_lidar):
    global reverse_running

    if(reverse_running):
        print("Reverse already running")
        return
    
    reverse_running = True

    distances = raw_lidar
    indices = np.arange(-5, 6, dtype=int) + 70

    r_side = np.mean(distances[(-indices) % 360])
    l_side = np.mean(distances[(+indices) % 360])

    steer = STEERING_LIMIT_IN_REVERSE if r_side > l_side else -STEERING_LIMIT_IN_REVERSE

    interface["steer"].set_duty_cycle(0.7*steer * STEER_VARIATION_RATE + STEER_CENTER)
    interface["speed"].set_duty_cycle(PWM_REVERSE)

    reverse_running = False

    for _ in range(20):
        time.sleep(0.1)
    
    interface["speed"].set_duty_cycle(7.5)
    
def get_nonzero_points_in_hitbox(distances):
    if distances is None:
        raise ValueError("Error: LiDAR input is None.")

    x, y = convert_rad_to_xy(distances, np.arange(0, 360))

    mask_hitbox =  (y > 0) & (np.abs(y) <= HITBOX_H1) & (np.abs(x) <= HITBOX_W) & (y * x != 0.0)

    return x[mask_hitbox], y[mask_hitbox]

@staticmethod
def convert_rad_to_xy(distance, angle_rad):
    y = distance * np.cos(angle_rad)
    x = distance * np.sin(angle_rad)
    return x, y

def get_raw_readings_from_top_right_corner(raw_distances, right):
    # 360 angles from 0 to 2π (exclusive)
    rad_raw_angles = np.linspace(0, 2*np.pi, num=360, endpoint=False)

    if right:
        d_sin_alpha_minus_w = raw_distances * np.sin(rad_raw_angles) - HITBOX_W
    else:
        d_sin_alpha_minus_w = raw_distances * np.sin(rad_raw_angles) + HITBOX_W
    
    d_cos_alpha_minus_h = raw_distances * np.cos(rad_raw_angles) - HITBOX_H1

    # Use arctan2(y, x) to get the new angles in [-π, π]c
    beta = np.arctan2(d_sin_alpha_minus_w, d_cos_alpha_minus_h)

    # Compute new distances from top-right corner
    # d_linha = "hypotenuse" in polar coords from that new origin.
    # Because we used arctan2(y, x), then sin(beta) = y/d_linha and cos(beta) = x/d_linha.
    # So  d_linha = y / sin(beta)  = x / cos(beta).
    # (We must be sure beta ≠ 0 for the sin() denominator.)
    # Typically you would do  d_linha = np.hypot(d_sin_alpha_minus_w, d_cos_alpha_minus_h).
    # But if you want to stick to the ratio approach:
    d_linha = d_sin_alpha_minus_w / np.sin(beta)

    # Ensure angles are in [0, 2π) instead of [-π, π)
    beta = (beta + 2*np.pi) % (2*np.pi)

    # Convert each continuous angle to a discrete bin (0..359)
    # Round to the nearest integer bin:
    angle_indices = np.round(
        beta / (2*np.pi/360)   # scale from radians to "index units"
    ).astype(int) % 360        # wrap around in case of 360

    # Create a new distance array; place each distance in its appropriate bin.
    # This ensures new_d_linha[i] corresponds to angle i * (2π/360).
    new_d_linha = np.zeros_like(d_linha)
    new_d_linha[angle_indices] = d_linha

    return new_d_linha