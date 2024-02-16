import numpy as np


#===================================================#
#                                                   #
#               Point cloud filtering               #
#                                                   #
#===================================================#

MAX_DISTANCE = 3.2

LIDAR_HEADING = 100
APERTURE_RATIO = 160.0 / 360.0


#===================================================#
#                                                   #
#             Occupancy grid parameters             #
#                                                   #
#===================================================#

MIN_X = -1.4
MAX_X =  1.4

MIN_Y = -0.6
MAX_Y =  2.2

RESOLUTION = 0.02

GRID_SIZE_X = np.ceil((MAX_X - MIN_X) / RESOLUTION).astype(int)
GRID_SIZE_Y = np.ceil((MAX_Y - MIN_Y) / RESOLUTION).astype(int)

ORIGIN = np.array([MIN_X, MIN_Y])


#===================================================#
#                                                   #
#                 Heatmap diffusion                 #
#                                                   #
#===================================================#

DIFFUSION_DEGREE = 4

MIN_HEAT = 16
MAX_HEAT = 255

INTENSITY = 10

kernel = np.array(
    [[1.0, 2.0, 1.0],
     [2.0, 4.0, 2.0],
     [1.0, 2.0, 1.0]]) / 16.0

NEW_SHAPE = (GRID_SIZE_X + 2 * INTENSITY, GRID_SIZE_Y + 2 * INTENSITY)

KERNEL_FFT = np.fft.fft2(kernel, s=NEW_SHAPE)**INTENSITY


#===================================================#
#                                                   #
#               Tentacles parameters                #
#                                                   #
#===================================================#

VEHICLE_WIDTH = 0.2

STEERING_LIMIT = np.deg2rad(18.0)

TENTACLE_LENGTH = 1.2
TENTACLE_POINTS = 20

TENTACLE_QUANTITY = 11

STEERING = np.linspace(
    -STEERING_LIMIT, STEERING_LIMIT, TENTACLE_QUANTITY, endpoint=True)

STEERING[STEERING == 0.0] = 1.0e-3
RADIUS = VEHICLE_WIDTH / np.tan(STEERING)
