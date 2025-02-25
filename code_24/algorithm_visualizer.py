import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

import control

class VoitureAlgorithmPlotter:
    def __init__(self):
        self.fig, self.ax_main = plt.subplots()
        self.fig.suptitle("Voiture Visualizer")
        
        self.ax_button = self.fig.add_axes([0.7, 0.92, 0.25, 0.04])
        self.button = Button(
            self.ax_button,
            'Raw / Algorithm',
            color='lightgoldenrodyellow',
            hovercolor='0.975'
        )
        self.button.on_clicked(self.toggle_visibility)
        
        self.show_algorithm = True
        self.filtered_plot = None
        self.target_arrow_plot = None
               
    def set_algorithm_visibility(self, visible):
        if self.filtered_plot is not None:
            self.filtered_plot[0].set_visible(visible)
        if self.target_arrow_plot is not None:
            self.target_arrow_plot.set_visible(visible)
    
    def toggle_visibility(self, event):
        self.show_algorithm = not self.show_algorithm
        self.set_algorithm_visibility(self.show_algorithm)
        self.fig.canvas.draw_idle()
    
    def convert_deg_to_xy(self, distance, angle_deg):
        angle_rad = np.radians(angle_deg) + np.pi / 2
        x = distance * np.cos(angle_rad) * (-1)
        y = distance * np.sin(angle_rad)
        return x, y
    
    def lidar_plotter(self, ax, pointcloud_distance, pointcloud_angles_deg):
        x, y = self.convert_deg_to_xy(pointcloud_distance, pointcloud_angles_deg)
        ax.grid(True)
        out = ax.plot(x, y, 'o')
        return out

    def target_vector_plotter(self, ax, target_angle_deg):
        x, y = self.convert_deg_to_xy(1.0, target_angle_deg)  # L=1
        out = ax.arrow(0, 0, x, y, head_width=0.05, head_length=0.1, fc='blue', ec='blue')
        return out

    def updateView(self, lidar_point_cloud):
        filtered_dist, filtred_angles = control.convolution_filter(lidar_point_cloud)
        target_angle_deg = control.compute_target_angle_deg(filtered_dist, filtred_angles)
               
        self.ax_main.clear()
        self.lidar_plotter(self.ax_main, lidar_point_cloud, np.linspace(0, 360, 360, endpoint=False))
        self.filtered_plot = self.lidar_plotter(self.ax_main, filtered_dist, filtred_angles)
        self.target_arrow_plot = self.target_vector_plotter(self.ax_main, target_angle_deg)
        self.set_algorithm_visibility(self.show_algorithm)
        self.fig.canvas.draw_idle()