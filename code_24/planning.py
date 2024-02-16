# pip install opencv-python==4.7.0.72
import cv2 as cv

import numpy as np

from scipy.signal import convolve, convolve2d

from typing import Any, Dict, List, Tuple

from matplotlib import pyplot as plt


# Point cloud parameters
MAX_DISTANCE = 4.8

LIDAR_HEADING = 0
APERTURE_RATIO = 220.0 / 360.0

# Grid parameters
MIN_X = -0.4
MAX_X =  3.2

MIN_Y = -1.8
MAX_Y =  1.8

RESOLUTION = 0.02

ORIGIN = np.array([MIN_X, MIN_Y])

# Vehicle parameters
VEHICLE_WIDTH = 0.3

STEERING_LIMIT = np.deg2rad(18.0)

# Exploring tentacles
TENTACLE_LENGTH = 1.2
TENTACLE_POINTS = 20

TENTACLE_QUANTITY = 25

STEERING = np.linspace(
    -STEERING_LIMIT, STEERING_LIMIT, TENTACLE_QUANTITY, endpoint=True)

STEERING[STEERING == 0.0] = 1.0e-3
RADIUS = VEHICLE_WIDTH / np.tan(STEERING)


def smooth(distances: np.ndarray, intensity: int = 3) -> np.ndarray:
    kernel = np.array([0.1, 0.2, 0.4, 0.2, 0.1])

    for _ in range(intensity):
        distances = convolve(distances, kernel, mode="same")

    return distances


def filter(distances: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    angles = np.linspace(0.0, 360.0, len(distances))

    # Limits the maximum distance
    distances = np.clip(distances, 0.0, MAX_DISTANCE)

    length = APERTURE_RATIO * len(distances)
    length = np.round(length).astype(int)

    shift = -LIDAR_HEADING + length // 2

    return np.roll(distances, shift)[:length], np.roll(angles, shift)[:length]


def bresenham(grid: np.ndarray, origin: Tuple[int, int], end: Tuple[int, int]) -> np.ndarray:
    x, y = origin

    dx =  abs(end[0] - x)
    dy = -abs(end[1] - y)

    sx = 1 if x < end[0] else -1
    sy = 1 if y < end[1] else -1

    error = dx + dy

    while x != end[0] or y != end[1]:
        try:
            grid[x, y] = 255
        except IndexError:
            break

        if 2 * error >= dy:
            if x == end[0]:
                break

            error, x = error + dy, x + sx

        if 2 * error <= dx:
            if y == end[1]:
                break

            error, y = error + dx, y + sy

    return grid


def create_grid(points: np.ndarray, filled: bool = False) -> np.ndarray:
    dim_x = np.ceil((MAX_X - MIN_X) / RESOLUTION).astype(int)
    dim_y = np.ceil((MAX_Y - MIN_Y) / RESOLUTION).astype(int)

    grid = np.zeros((dim_x, dim_y), np.uint8)
    origin = np.round(-ORIGIN / RESOLUTION).astype(int)

    indices = np.round((points - ORIGIN) / RESOLUTION).astype(int)
    indices = np.unique(indices, axis=0)

    if not filled:
        mask_x = (0 <= indices[:, 0]) & (indices[:, 0] < dim_x)
        mask_y = (0 <= indices[:, 1]) & (indices[:, 1] < dim_y)

        indices = indices[mask_x & mask_y]

        grid[indices[:, 0], indices[:, 1]] = 255

        return grid

    for end in indices:
        grid = bresenham(grid, origin, end)

    return grid


def improve_mask(mask: np.ndarray, intensity: int = 3) -> np.ndarray:
    kernel = np.array(
        [[0, 1, 0],
         [1, 1, 1],
         [0, 1, 0]], np.uint8)

    mask = cv.dilate(mask, kernel, iterations=intensity)
    mask = cv.erode(mask, kernel, iterations=intensity)

    # Erodes the mask border to protects the vehicle
    mask = cv.erode(mask, kernel,
        iterations=np.ceil(0.5 * VEHICLE_WIDTH / RESOLUTION).astype(int))

    return mask


def cartesian(distances: np.ndarray, angles: np.ndarray) -> np.ndarray:
    angles = np.deg2rad(angles)

    x = distances * np.cos(angles)
    y = distances * np.sin(angles)

    points = np.concatenate(
        (x[:, np.newaxis], y[:, np.newaxis]), axis=1)

    return points


def create_heatmap(distances: np.ndarray) -> np.ndarray:
    angles = np.linspace(0.0, 360.0, len(distances))
    points = cartesian(distances, angles)

    grid = create_grid(points) // 255

    kernel = np.array(
        [[0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
         [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
         [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
         [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
         [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
         [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
         [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
         [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
         [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
         [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
         [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0]], np.uint8)

    for _ in range(4):
        grid = grid + cv.dilate(grid, kernel)
        grid = grid / np.max(grid)

    minimum = 16
    heatmap = np.round((255 - minimum) * grid + minimum).astype(np.uint8)

    kernel = np.array(
        [[1.0, 2.0, 1.0],
         [2.0, 4.0, 2.0],
         [1.0, 2.0, 1.0]]) / 16.0

    for _ in range(10):
        heatmap = convolve2d(heatmap, kernel, mode="same")

    points = cartesian(*filter(smooth(distances)))

    mask = create_grid(points, filled=True)
    mask = (improve_mask(mask) // 255).astype(np.uint8)

    return heatmap * mask


def create_tentacles() -> List[np.ndarray]:
    tentacles = []

    for index, radius in enumerate(RADIUS):
        TENTACLE_LENGTH = 1.6 - 0.8 * np.abs(STEERING[index])

        angles = np.linspace(0.0, TENTACLE_LENGTH / radius, TENTACLE_POINTS)

        x = radius * np.cos(angles)
        y = radius * np.sin(angles)

        points = np.concatenate(
            (y[:, np.newaxis], radius - x[:, np.newaxis]), axis=1)

        tentacles.append(points)

    return tentacles


def select_tentacle(heatmap: np.ndarray, tentacles: np.ndarray) -> int:
    scores = []

    for points in tentacles:
        indices = np.round((points - ORIGIN) / RESOLUTION).astype(int)

        values = heatmap[indices[:, 0], indices[:, 1]]
        values[values == 0] = 255

        scores.append(np.sum(values))

    return np.argmin(scores)


def show(data):
    fig, ax = plt.subplots(figsize=(8,6))
    
    ax.set_aspect("equal")

    ax.imshow(np.rot90(data["heatmap"]))
    
    # angles = np.linspace(0, 2*np.pi, 360)
    
    # x = data["distances"] * np.cos(angles)
    # y = data["distances"] * np.sin(angles)
    
    # ax.plot(x, y, "bo")
    
    # for tentacle in data["tentacles"]:
    #     ax.plot(tentacle[:, 0], tentacle[:, 1], "k-", alpha=0.1)
    
    # ax.plot(data["path"][:, 0], data["path"][:, 1], "g-")

    plt.tight_layout()
    plt.show()

    del fig, ax


def Direction_Law(distances: np.ndarray) -> float:
    distances = np.asarray(distances) / 1000.0

    heatmap = create_heatmap(distances)
    tentacles = create_tentacles()

    argmin = select_tentacle(heatmap, tentacles)

    collision = check_collision(heatmap, tentacles[argmin])

    data = {
        "distances": distances,
        "heatmap": heatmap,
        "tentacles": tentacles,
        "path": tentacles[argmin],
    }

    indices = np.round((data["path"] - ORIGIN) / RESOLUTION).astype(int)

    data["heatmap"][indices[:, 0], indices[:, 1]] = 255

    # show(data)
    
    a = 0.0775
    b = 8
    cyclerate_dir = -a*np.rad2deg(STEERING[argmin]) + b

    return collision, cyclerate_dir, np.rad2deg(STEERING[argmin])


def Speed_Law(steering: float) -> float:
    return 8.4

    a = 2.0
    b = np.rad2deg(STEERING_LIMIT)
    c = 0.8
    d = 0.8 / (1.0 - np.exp(-a))

    value = c + d * (np.exp(-a * (steering / b)**2) - np.exp(-a))

    return value


def check_collision(heatmap: np.ndarray, tentacle: np.ndarray) -> bool:
    indices = np.round((tentacle - ORIGIN) / RESOLUTION).astype(int)

    values = heatmap[indices[:, 0], indices[:, 1]]

    return 0.0 in values[5:]


def check_side(distances: np.ndarray) -> float:
    lef_side = distances[50:65]
    rig_side = distances[-65:-50]
    
    if rig_side > lef_side:
        return  18.0
    else:
        return -18.0