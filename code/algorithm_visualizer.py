import seaborn as sns
import numpy as np

import matplotlib

import matplotlib.pyplot as plt
from matplotlib.widgets import Button

import algorithm.control_direction as control_direction
import algorithm.control_speed as control_speed

matplotlib.use('TkAgg')

class VoitureAlgorithmPlotter:
    def __init__(self):
        self.fig, self.ax_main = plt.subplots()
        self.fig.suptitle("Voiture Visualizer")
        
        self.ax_button = self.fig.add_axes([0.7, 0.92, 0.25, 0.04])
        self.button = Button(self.ax_button, 'Algorithm / Raw', color='lightgoldenrodyellow', hovercolor='0.975')
        self.button.on_clicked(self.toggle_visibility)
        
        self.show_algorithm = True
        
        self.ax_main.grid(True)
        
        # Plots
        self.raw_plot = None
        self.convoluted_plot = None
        self.target_arrow_plot = None
        self.hitbox = None
        self.hitbox_plot = np.array([])
        
    def set_algorithm_visibility(self, visible):
        if self.convoluted_plot is not None:
            self.convoluted_plot[0].set_visible(visible)
        if self.target_arrow_plot is not None:
            self.target_arrow_plot.set_visible(visible)
    
    def toggle_visibility(self, event):
        self.show_algorithm = not self.show_algorithm
        self.set_algorithm_visibility(self.show_algorithm)
        self.fig.canvas.draw_idle()
    
    def lidar_plotter(self, ax, pointcloud_distance, pointcloud_angles_rad):
        x, y = control_direction.convert_rad_to_xy(pointcloud_distance, pointcloud_angles_rad)
        out = ax.plot(x, y, 'o')
        return out

    # def target_vector_plotter(self, ax, originx, originy, target_angle_deg, color):
    #     x, y = control_direction.convert_rad_to_xy(1.0, np.radians(target_angle_deg))
    #     out = ax.arrow(originx, originy, x, y, head_width=0.05, head_length=0.1, fc=color, ec=color)
    #     return out
    
    def target_vector_plotter(self, ax, x, y, angle_deg, color='red', length=1.0):        
        dx, dy = control_direction.convert_rad_to_xy(1.0, np.radians(angle_deg))
        
        return ax.arrow(x, y, dx*length, dy*length, head_width=0.1, head_length=0.2, 
                    fc=color, ec=color, alpha=0.7)
    
    def hitbox_plotter(self, ax, lidar_point_cloud):
        x, y = control_direction.get_nonzero_points_in_hitbox(lidar_point_cloud)
        
        if(x.size == 0 or y.size == 0):
            return None
        
        np.array([ax.plot(x, y, 'o') for _ in range(2)])    

    def updateZoom(self, filtered_dist, filtred_angles):
        if self.show_algorithm and filtered_dist.size > 0:
            x_filtered, y_filtered = control_direction.convert_rad_to_xy(filtered_dist, np.radians(filtred_angles))
            x_min, x_max = np.min(x_filtered), np.max(x_filtered)
            y_min, y_max = np.min(y_filtered), np.max(y_filtered)
        
            pad_x = (x_max - x_min) * 0.1
            pad_y = (y_max - y_min) * 0.1
            #self.ax_main.set_xlim(x_min - pad_x, x_max + pad_x)
            #self.ax_main.set_ylim(y_min - pad_y, y_max + pad_y)
        else:
            self.ax_main.relim()
            self.ax_main.autoscale_view()

    def updateView(self, raw_lidar):
        shrinked = control_direction.shrink_space(raw_lidar)
        filtered_dist, filtred_angles = control_direction.convolution_filter(shrinked)        
        target_angle_deg, delta = control_direction.compute_angle(filtered_dist, filtred_angles, shrinked)
        speed = control_speed.compute_speed(shrinked, target_angle_deg)

        # Determine arrow length based on speed
        arrow_length = abs(speed) * 0.5  # Adjust the multiplier as needed for proper scaling
        # Determine arrow direction based on speed sign
        arrow_angle = target_angle_deg if speed >= 0 else (target_angle_deg + 180) % 360
        blue_arrow_angle = (target_angle_deg - delta) if speed >= 0 else ((target_angle_deg - delta) + 180) % 360

        self.ax_main.clear()
        self.ax_main.set_xlim(-3, 3.0)
        self.ax_main.set_ylim(-0.5, 5)
        self.ax_main.set_aspect("equal")

        self.raw_plot = self.lidar_plotter(self.ax_main, raw_lidar, np.linspace(0, 2*np.pi, 360, endpoint=False))

        # Shows the shrinked lidar points
        # #self.lidar_plotter(self.ax_main, shrinked, np.linspace(0, 2*np.pi, 360, endpoint=False))

        self.convoluted_plot = self.lidar_plotter(self.ax_main, filtered_dist, np.radians(filtred_angles))
        # Use arrow_length and arrow_angle for the arrow
        self.target_arrow_plot = self.target_vector_plotter(self.ax_main, 0, 0, arrow_angle, 'red', length=arrow_length)        
        self.hitbox_plot = self.hitbox_plotter(self.ax_main, shrinked)
        self.hitbox_rect = self.lidar_plotter(self.ax_main, control_direction.hitbox, np.linspace(0, 2*np.pi, 360, endpoint=False))      
        self.target_arrow_plot = self.target_vector_plotter(self.ax_main, 0, 0, blue_arrow_angle, color='blue', length=arrow_length)

        self.updateZoom(filtered_dist, filtred_angles)
        self.set_algorithm_visibility(self.show_algorithm)

        self.fig.canvas.draw_idle()
