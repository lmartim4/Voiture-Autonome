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

def compute_angle(filtred_distances, filtred_angles, raw_lidar):
    target_angle = filtred_angles[np.argmax(filtred_distances)]
    delta = 0
    # l_angle = AVOID_CORNER_MAX_ANGLE
    # r_angle = AVOID_CORNER_MAX_ANGLE
    
    # for index in range(0, AVOID_CORNER_MAX_ANGLE):
    #     l_dist = raw_lidar[(target_angle + index) % 360]
    #     r_dist = raw_lidar[(target_angle - index) % 360]

    #     if l_dist < AVOID_CORNER_MIN_DISTANCE:
    #         l_angle = index

    #     if r_dist < AVOID_CORNER_MIN_DISTANCE:
    #         r_angle = index
                
    # print(f" l_dist: {l_dist} r_dist: {r_dist}")

    # if l_angle > r_angle:
    #     delta = -AVOID_CORNER_SCALE_FACTOR * (AVOID_CORNER_MAX_ANGLE - r_angle)
    # else:
    #     delta = +AVOID_CORNER_SCALE_FACTOR * (AVOID_CORNER_MAX_ANGLE - l_angle)

    # print("delta = ", delta)
    
    # target_angle += delta
    
    target_angle = (target_angle + 180) % 360 - 180
    
    return target_angle, delta

def compute_steer(alpha):
    return np.sign(alpha) * lerp(np.abs(alpha), STEER_FACTOR)

def compute_pwm(steer):
    return steer * STEER_VARIATION_RATE + STEER_CENTER

def compute_steer_from_lidar(raw_lidar):    
    filtreed_distances, filtreed_angles = convolution_filter(raw_lidar)
    target, _ = compute_angle(filtreed_distances, filtreed_angles, raw_lidar)
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
    return False
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
    
def reverse(interface: Dict[str, Any], raw_lidar):
    global reverse_running

    if(reverse_running):
        print("Reverse already running")
        return
    
    reverse_running = True
    activate_reverse(interface["speed"])

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

    deactivate_reverse(interface["speed"])
    
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

@staticmethod
def calculate_hitbox_polar(w, h1, h2):
    """
    Return an array of radial distances for angles -pi..pi (360 steps),
    giving the intersection of a ray at angle theta with the rectangle
    [-w, w] x [-h2, h1].
    """
    print("CALCULATING HITBOX")
    
    # Angles from -pi to pi in 360 increments
    rad_raw_angles = np.linspace(0, 2*np.pi, num=360, endpoint=False)
    
    polar_coords = []
    polar_angles = []
    
    for theta in rad_raw_angles:
        c = np.cos(theta)
        s = np.sin(theta)
        
        # We use t >= 0 in the parametric form:
        #   X(t) = t*cos(theta)
        #   Y(t) = t*sin(theta)
        #
        # We'll collect all valid positive 't' that hits the rectangle
        # boundary, then take the smallest positive.
        candidates = []
        
        # 1) Intersection with the vertical sides x = +/- w (if cos(theta) != 0)
        if abs(c) > 1e-14:
            # Decide which vertical side we actually hit (depending on sign of cos)
            # If cos > 0, we expect x=+w. If cos < 0, x=-w.
            x_side = w if c > 0 else -w
            t_x = x_side / c  # solve t for x_side = t*cos(theta)
            if t_x >= 0:
                y_at_x = s * t_x
                # Check if that y lies within the rectangle's vertical span
                if -h2 <= y_at_x <= h1:
                    candidates.append(t_x)
        
        # 2) Intersection with the horizontal sides y = +h1 or y = -h2 (if sin(theta) != 0)
        if abs(s) > 1e-14:
            # If sin>0, we expect y=+h1. If sin<0, y=-h2.
            y_side = h1 if s > 0 else -h2
            t_y = y_side / s  # solve t for y_side = t*sin(theta)
            if t_y >= 0:
                x_at_y = c * t_y
                # Check if that x lies within the rectangle's horizontal span
                if -w <= x_at_y <= w:
                    candidates.append(t_y)
        
        # If for some reason no valid intersection was found, set distance=0
        # (or you might choose np.nan if you prefer).
        if len(candidates) == 0:
            d = 0.0
        else:
            # We want the FIRST intersection => smallest positive t
            t = min(candidates)
            d = t  # Because distance = sqrt((t*c)^2 + (t*s)^2) = t
        
        polar_coords.append(d)
        polar_angles.append(theta - np.pi/2)
    
    # Map each angle to an integer bin in [0..359]
    angle_indices = np.round(
        np.array(polar_angles) / (2 * np.pi / 360)
    ).astype(int) % 360
    
    # Create final 1D array, indexed by angle
    new_d_linha = np.zeros_like(polar_coords)
    new_d_linha[angle_indices] = polar_coords
    
    return new_d_linha

hitbox = calculate_hitbox_polar(HITBOX_W, HITBOX_H1, HITBOX_H2)

def shrink_space(raw_lidar):
    free_space_shrink_mask = raw_lidar > 0
    shrink_space_lidar = np.copy(raw_lidar)
    shrink_space_lidar[free_space_shrink_mask] -= hitbox[free_space_shrink_mask]

    return shrink_space_lidar

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
    