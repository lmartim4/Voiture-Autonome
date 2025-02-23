import matplotlib.pyplot as plt
from lidar_plot import LidarVisualizer

lidar_vis = LidarVisualizer("/home/ensta/Voiture-Autonome/logs/2025-02-23/23-20-45/Lidar-Sensor.log")

fig, axs = plt.subplots(2, 2, figsize=(10, 10), subplot_kw={'projection': 'polar'})

lidar_vis.add_subplot(axs[0, 0])

lidar_vis.enable_slider(fig)

plt.show()
