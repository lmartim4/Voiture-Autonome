import cv2 as cv

from numba import njit

from typing import Any, Dict, List, Tuple

from scipy.signal import convolve

from constants import *


def filter(distances: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Filters a circular sector of the point cloud and limits its distances.

    Args:
        distances (np.ndarray): vector with distances ordered by angle.

    Returns:
        Tuple[np.ndarray, np.ndarray]: tuple containing the
            vector with distances and the vector with angles,
            both filtered for the field of view of interest.
    """

    angles = np.linspace(0.0, 2 * np.pi, len(distances))

    # Limits the maximum distance
    distances = np.clip(distances, 0.0, MAX_DISTANCE)

    length = APERTURE_RATIO * len(distances)
    length = np.round(length).astype(int)

    shift = -LIDAR_HEADING + length // 2

    return np.roll(distances, shift)[:length], np.roll(angles, shift)[:length]


def smooth(distances: np.ndarray, intensity: int = 3) -> np.ndarray:
    """
    Smoothes ordered points using convolutions (weighted mean with neighbors).

    Args:
        distances (np.ndarray): vector with distances ordered by angle.
        intensity (int, optional): quantity of convolutions. Defaults to 3.

    Returns:
        np.ndarray: smoothed vector with distances ordered by angle.
    """

    kernel = np.array([0.1, 0.2, 0.4, 0.2, 0.1])

    for _ in range(intensity):
        distances = convolve(distances, kernel, mode="same")

    return distances


def polar2cartesian(distances: np.ndarray, angles: np.ndarray) -> np.ndarray:
    """
    Converts points in polar coordinates to Cartesian coordinates.

    Args:
        distances (np.ndarray): vector with distances ordered by angle.
        angles (np.ndarray): vector with angles measured in radians.

    Returns:
        np.ndarray: points with Cartesian coordinates arranged on the rows.
    """

    x = distances * np.cos(angles)
    y = distances * np.sin(angles)

    points = np.concatenate(
        (x[:, np.newaxis], y[:, np.newaxis]), axis=1)

    return points


@njit(fastmath=True)
def draw_line(grid: np.ndarray, srt: Tuple[int, int], end: Tuple[int, int]) -> np.ndarray:
    """
    Draws a line on the occupancy grid using the Bresenham algorithm.
    Uses Numba just in time (JIT) compilation to speed up its execution.

    Args:
        grid (np.ndarray): discretized space occupation grid.

        srt (Tuple[int, int]): coordinate of the line's starting point.
        end (Tuple[int, int]): coordinate of the line's ending point.

    Returns:
        np.ndarray: updated discretized space occupation grid.
    """

    x, y = srt

    dx =  abs(end[0] - x)
    dy = -abs(end[1] - y)

    sx = 1 if x < end[0] else -1
    sy = 1 if y < end[1] else -1

    error = dx + dy

    while x != end[0] or y != end[1]:
        if x < 0 or GRID_SIZE_X <= x:
            break

        if y < 0 or GRID_SIZE_Y <= y:
            break

        grid[x, y] = 1

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
    """
    Creates a discretized space occupancy grid from the lidar point cloud.

    Args:
        points (np.ndarray): lidar cropped point cloud with
            Cartesian coordinates arranged on the rows.

        filled (bool, optional): indicates whether the occupancy
            grid should be filled in or not. Defaults to False.

    Returns:
        np.ndarray: discretized space occupation grid.
    """

    grid = np.zeros((GRID_SIZE_X, GRID_SIZE_Y), np.uint8)
    origin = np.round(-ORIGIN / RESOLUTION).astype(int)

    # Discretizes space into grid cells
    indices = np.round((points - ORIGIN) / RESOLUTION).astype(int)
    indices = np.unique(indices, axis=0)

    if not filled:
        mask_x = (0 <= indices[:, 0]) & (indices[:, 0] < GRID_SIZE_X)
        mask_y = (0 <= indices[:, 1]) & (indices[:, 1] < GRID_SIZE_Y)

        indices = indices[mask_x & mask_y]

        grid[indices[:, 0], indices[:, 1]] = 1

        return grid

    for end in indices:
        grid = draw_line(grid, origin, end)

    kernel = np.array(
        [[0, 1, 0],
         [1, 1, 1],
         [0, 1, 0]], np.uint8)

    # Closes holes in the occupancy grid
    grid = cv.dilate(grid, kernel, iterations=3)
    grid = cv.erode(grid, kernel, iterations=3)

    return grid


def create_heatmap(distances: np.ndarray) -> np.ndarray:
    distances, angles = filter(distances)

    grid = create_grid(polar2cartesian(distances, angles))

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

    heatmap = np.copy(grid)

    for _ in range(DIFFUSION_DEGREE):
        grid = cv.dilate(grid, kernel)
        heatmap = heatmap + grid

    heatmap = heatmap / (DIFFUSION_DEGREE + 1)
    heatmap = (MAX_HEAT - MIN_HEAT) * heatmap + MIN_HEAT

    heatmap = np.round(heatmap).astype(np.uint8)

    # Smoothes heatmap steps
    heatmap = np.real(np.fft.ifft2(
        np.fft.fft2(heatmap, s=NEW_SHAPE) * KERNEL_FFT))

    heatmap = heatmap[INTENSITY:-INTENSITY, INTENSITY:-INTENSITY]

    distances = smooth(distances)

    # Creates the heatmap mask
    mask = create_grid(polar2cartesian(distances, angles), filled=True)

    kernel = np.array(
        [[0, 1, 0],
         [1, 1, 1],
         [0, 1, 0]], np.uint8)

    # Erodes the mask border to protects the vehicle
    mask = cv.erode(mask, kernel, iterations=5)

    return heatmap * mask


@njit(fastmath=True)
def create_tentacles() -> List[np.ndarray]:
    tentacles = []

    for radius in RADIUS:
        angles = np.linspace(0.0, TENTACLE_LENGTH / radius, TENTACLE_POINTS)

        x = radius * np.cos(angles)
        y = radius * np.sin(angles)

        points = np.concatenate(
            (radius - x[:, np.newaxis], y[:, np.newaxis]), axis=1)

        tentacles.append(points)

    return tentacles


def select_tentacle(heatmap: np.ndarray, tentacles: np.ndarray) -> int:
    scores = []

    for points in tentacles:
        indices = np.round((points - ORIGIN) / RESOLUTION).astype(int)

        values = heatmap[indices[:, 0], indices[:, 1]]
        values[values == 0] = MAX_HEAT

        scores.append(np.sum(values))

    return np.argmin(scores)


def compute_steer(measurements: Dict[str, Any]) -> float:
    heatmap = create_heatmap(measurements["lidar"])
    tentacles = create_tentacles()

    argmin = select_tentacle(heatmap, tentacles)

    return np.rad2deg(STEERING[argmin])


def compute_speed(steer: float, measurements: Dict[str, Any]) -> float:
    return 0.0
