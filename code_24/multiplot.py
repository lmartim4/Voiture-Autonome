import matplotlib.pyplot as plt
from lidar_plot import LidarVisualizer

lidar_vis = LidarVisualizer("/home/ensta/Voiture-Autonome/logs/2025-02-23/23-20-45/Lidar-Sensor.log")

fig, axs = plt.subplots(1, 1, figsize=(20, 20), subplot_kw={'projection': 'polar'})

# Use axs[0] for the first subplot (since axs is a 1D array)
lidar_vis.add_subplot(axs)
lidar_vis.enable_slider_and_buttons(fig)

plt.show()
