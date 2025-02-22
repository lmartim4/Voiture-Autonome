from environment import Environment 
from lidar import Lidar
import pygame
import numpy as np
import params

# To understand the implementation : https://www.youtube.com/watch?v=JbUNsYPJK1U

environment = Environment("track1.png")
environment.original_map = environment.map.copy()
lidar = Lidar(200, 4, environment.original_map, uncertainty=(0.5,0.01)) 
environment.lidar = lidar
environment.map.fill(params.black)
environment.infomap = environment.map.copy()
environment.run()