from environment import Environment 
from lidar import Lidar
import pygame
import numpy as np

environment = Environment("track0.png")
environment.original_map = environment.map.copy()
lidar = Lidar(200, 4, environment.original_map, uncertainty=(0.5,0.01)) 
environment.lidar = lidar
environment.map.fill(environment.black)
environment.infomap = environment.map.copy()
environment.run()