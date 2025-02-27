import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import matplotlib.patches as patches

import control

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
        x, y = control.convert_rad_to_xy(pointcloud_distance, pointcloud_angles_rad)
        out = ax.plot(x, y, 'o')
        return out

    def target_vector_plotter(self, ax, originx, originy, target_angle_deg, color):
        x, y = control.convert_rad_to_xy(1.0, np.radians(target_angle_deg))
        out = ax.arrow(originx, originy, x, y, head_width=0.05, head_length=0.1, fc=color, ec=color)
        return out
    
    def hitbox_plotter(self, ax, lidar_point_cloud):
        x, y = control.get_nonzero_points_in_hitbox(lidar_point_cloud)
        
        if(x.size == 0 or y.size == 0):
            return None
        
        np.array([ax.plot(x, y, 'o') for _ in range(2)])    

    def updateZoom(self, filtered_dist, filtred_angles):
        if self.show_algorithm and filtered_dist.size > 0:
            x_filtered, y_filtered = control.convert_rad_to_xy(filtered_dist, np.radians(filtred_angles))
            x_min, x_max = np.min(x_filtered), np.max(x_filtered)
            y_min, y_max = np.min(y_filtered), np.max(y_filtered)
        
            pad_x = (x_max - x_min) * 0.1
            pad_y = (y_max - y_min) * 0.1
            self.ax_main.set_xlim(x_min - pad_x, x_max + pad_x)
            self.ax_main.set_ylim(y_min - pad_y, y_max + pad_y)
        else:
            self.ax_main.relim()
            self.ax_main.autoscale_view()
 
    def updateView(self, raw_lidar):
        shrinked = control.shrink_space(raw_lidar)
        filtered_dist, filtred_angles = control.convolution_filter(shrinked)
        
        #right_corner_distances = control.get_raw_readings_from_top_right_corner(raw_lidar, True)
        #left_corner_distances = control.get_raw_readings_from_top_right_corner(raw_lidar, False)
        
        target_angle_deg, delta = control.compute_angle(filtered_dist, filtred_angles, shrinked)

        self.ax_main.clear()
        
       
        
        self.raw_plot           = self.lidar_plotter(self.ax_main, raw_lidar, np.linspace(0, 2*np.pi, 360, endpoint=False))
        self.lidar_plotter(self.ax_main, shrinked, np.linspace(0, 2*np.pi, 360, endpoint=False))
        
        self.convoluted_plot    = self.lidar_plotter(self.ax_main, filtered_dist, np.radians(filtred_angles))
        
        self.target_arrow_plot  = self.target_vector_plotter(self.ax_main, 0, 0, target_angle_deg, 'red')
        
        self.hitbox_plot        = self.hitbox_plotter(self.ax_main, shrinked)
        
        self.hitbox_rect        = self.lidar_plotter(self.ax_main, control.hitbox, np.linspace(0, 2*np.pi, 360, endpoint=False))
        
        # self.hitbox_rect        = patches.Rectangle(
        #                             (-control.HITBOX_WIDTH, 0), 2 * control.HITBOX_WIDTH,  control.HITBOX_HEIGHT,
        #                             edgecolor='red', facecolor='none', linewidth=2, linestyle='dashed', label="Hitbox")   
        # self.ax_main.add_patch(self.hitbox_rect)
        
        # self.lidar_plotter(self.ax_main, right_corner_distances, np.linspace(0, 2*np.pi, 360, endpoint=False))
        # self.lidar_plotter(self.ax_main, left_corner_distances, np.linspace(0, 2*np.pi, 360, endpoint=False))
        
        
        
        #self.target_arrow_plot  = self.target_vector_plotter(self.ax_main, control.HITBOX_WIDTH, control.HITBOX_HEIGHT, target_angle_deg - delta, color='green')
        #self.target_arrow_plot  = self.target_vector_plotter(self.ax_main, -control.HITBOX_WIDTH, control.HITBOX_HEIGHT, target_angle_deg - delta, color='green')
        
        
        self.target_arrow_plot  = self.target_vector_plotter(self.ax_main, 0, 0, target_angle_deg - delta, color='blue')
        
        self.updateZoom(filtered_dist, filtred_angles)
        self.set_algorithm_visibility(self.show_algorithm)
        
        self.fig.canvas.draw_idle()