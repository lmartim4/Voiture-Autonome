import sys
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.backend_bases import KeyEvent
from typing import Tuple
from control import convolution_filter, compute_steer_from_lidar  # Assuming you have this custom function

warnings.filterwarnings("ignore")
plt.style.use(["seaborn-v0_8-whitegrid", "seaborn-v0_8-muted"])

class LidarVisualizer:
    def __init__(self, filename=None, df=None):
        """
        Initializes the LiDAR visualizer.
        """
        if filename:
            self.df = self.read_lidar_log(filename)
        elif df is not None:
            self.df = df
        else:
            raise ValueError("Either a filename or a DataFrame must be provided.")

        self.timestamps = self.df["timestamp"].to_numpy()
        self.timestamps -= self.timestamps[0]
        self.timestamps /= 1000.0  # Convert ms to seconds

        # Angles for 360 points
        self.angles = np.linspace(0, 2 * np.pi, 360, endpoint=False)

        # Figure and Axes
        self.fig = None
        self.ax = None

        # Interactivity
        self.slider = None
        self.filter_button = None
        self.mode_button = None

        # Toggle states
        self.show_filtered = False   # Raw vs. Filtered
        self.show_polar = False       # Polar vs. Cartesian

        # Plot objects
        self.lidar_plot_raw = None
        self.lidar_plot_filtered = None
        self.target_marker = None

    @staticmethod
    def read_lidar_log(filename: str) -> pd.DataFrame:
        """
        Reads a LiDAR log file.
        """
        records = []
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                split_line = line.split(maxsplit=1)
                if len(split_line) < 2:
                    continue

                timestamp_str, array_str = split_line[0], split_line[1]
                timestamp = float(timestamp_str)

                try:
                    pointcloud = np.array(json.loads(array_str))
                    if len(pointcloud) != 360:
                        continue
                    records.append({"timestamp": timestamp, "pointcloud": pointcloud})
                except Exception as e:
                    print(f"Error parsing line: {line}\n{e}")

        return pd.DataFrame(records)

    def add_subplots(self, fig: plt.Figure):
        """
        Creates and configures a single subplot (polar).
        """
        self.fig = fig
        self.ax = fig.add_subplot(1, 1, 1, projection='polar')
        self._create_line_objects()
        self.update_plot(self.timestamps[0])

    def add_subplot(self, ax: plt.Axes):
        """
        Initializes an existing Axes for LiDAR plotting.
        """
        self.fig = ax.figure
        self.ax = ax
        self._create_line_objects()
        self.update_plot(self.timestamps[0])

    def enable_slider_and_buttons(self, fig: plt.Figure):
        """
        Adds a slider and toggle buttons for user interaction.
        """
        self.fig = fig

        slider_ax = fig.add_axes([0.2, 0.02, 0.6, 0.03])
        self.slider = Slider(ax=slider_ax, label="Time (s)",
                             valmin=0, valmax=self.timestamps[-1],
                             valinit=0, valfmt="%.2f s")
        self.slider.on_changed(self.update_plot)

        button_ax = fig.add_axes([0.81, 0.92, 0.1, 0.04])
        self.filter_button = Button(button_ax, "Filter: OFF", color="lightgoldenrodyellow")
        self.filter_button.on_clicked(self.on_filter_button)

        mode_ax = fig.add_axes([0.68, 0.92, 0.1, 0.04])
        self.mode_button = Button(mode_ax, "Plot: Polar", color="lightblue")
        self.mode_button.on_clicked(self.on_plot_mode_button)

        fig.canvas.mpl_connect("key_press_event", self.on_key_press)

    def enable_slider(self, fig: plt.Figure):
        """
        Adds only a slider (for multiplot layouts).
        """
        self.fig = fig
        slider_ax = fig.add_axes([0.2, 0.02, 0.6, 0.03])
        self.slider = Slider(ax=slider_ax, label="Time (s)",
                             valmin=0, valmax=self.timestamps[-1],
                             valinit=0, valfmt="%.2f s")
        self.slider.on_changed(self.update_plot)

    def _create_line_objects(self):
        """
        Creates the raw and filtered LiDAR plot objects.
        """
        self.lidar_plot_raw, = self.ax.plot([], [], 'bo', markersize=3, label="Raw LiDAR")
        self.lidar_plot_filtered, = self.ax.plot([], [], 'ro', markersize=3, label="Filtered LiDAR")
        # Reset target marker so it can be re-created properly
        self.target_marker = None

    def _ensure_axes(self, mode: str):
        """
        Re-creates axes in the saved bbox if mode changes.
        """
        bbox = self.ax.get_position()
        self.fig.delaxes(self.ax)
        if mode == "polar":
            self.ax = self.fig.add_axes(bbox, projection='polar')
        else:
            self.ax = self.fig.add_axes(bbox)
        self._create_line_objects()

    def _update_target_marker(self, filtered_scan: np.ndarray, filtered_angles_rad: np.ndarray, mode: str):
        """
        Updates or creates the target marker on the axes, in polar or cartesian mode.
        """
        target_idx = np.argmax(filtered_scan)
        target_dist = filtered_scan[target_idx]
        target_ang = filtered_angles_rad[target_idx]
        
        if mode == "polar":
            marker_coords = ([target_ang], [target_dist])
        else:
            x_target = target_dist * np.sin(target_ang)
            y_target = target_dist * np.cos(target_ang)
            marker_coords = ([x_target], [y_target])

        if self.target_marker is None:
            self.target_marker, = self.ax.plot(marker_coords[0], marker_coords[1],
                                               'k*', markersize=12, label="Target")
        else:
            self.target_marker.set_data(marker_coords[0], marker_coords[1])

    def update_plot(self, value: float):
        """
        Updates the plot (polar or cartesian) based on the slider value.
        """
        idx = np.argmin(np.abs(self.timestamps - value))
        raw_scan = self.df.iloc[idx]["pointcloud"]

        if self.show_polar:
            if not hasattr(self.ax, 'set_theta_zero_location'):
                self._ensure_axes("polar")
                
            self.ax.set_theta_zero_location("N")
            self.ax.set_theta_direction(-1)
            max_range = self.df["pointcloud"].apply(lambda x: max(x)).max()
            self.ax.set_ylim([0, max_range * 1.2])
            self.ax.set_aspect('auto')
            self.lidar_plot_raw.set_data(self.angles, raw_scan)

            if self.show_filtered:
                filtered_scan, filtered_angles = convolution_filter(raw_scan)
                filtered_angles_rad = np.radians(filtered_angles)
                self.lidar_plot_filtered.set_data(filtered_angles_rad, filtered_scan)
                self._update_target_marker(filtered_scan, filtered_angles_rad, mode="polar")
            else:
                self.lidar_plot_filtered.set_data([], [])
                # Remove persistent target marker if no filtered data is displayed
                if self.target_marker is not None:
                    self.target_marker.remove()
                    self.target_marker = None
                
            self.ax.set_ylim([0, max(raw_scan) * 1.2])
            current_mode = "Raw + Filtered" if self.show_filtered else "Raw"
            self.ax.set_title(f"{current_mode} LiDAR (Polar) @ {self.timestamps[idx]:.2f}s")
            self.ax.legend()

        else:
            if hasattr(self.ax, 'set_theta_zero_location'):
                self._ensure_axes("cartesian")

            self.ax.set_aspect('equal', adjustable='box')
            self.ax.grid(True)

            # Compute raw cartesian coordinates
            x_raw = raw_scan * np.sin(self.angles)
            y_raw = raw_scan * np.cos(self.angles)
            self.lidar_plot_raw.set_data(x_raw, y_raw)

            # Set the exact limits based on the data points
            x_min, x_max = x_raw.min(), x_raw.max()
            y_min, y_max = y_raw.min(), y_raw.max()
            self.ax.set_xlim([1.1 * x_min, 1.1 * x_max])
            self.ax.set_ylim([1.1 * y_min, 1.1 * y_max])

            if self.show_filtered:
                filtered_scan, filtered_angles = convolution_filter(raw_scan)
                filtered_angles_rad = np.radians(filtered_angles)
                x_filt = filtered_scan * np.sin(filtered_angles_rad)
                y_filt = filtered_scan * np.cos(filtered_angles_rad)
                self.lidar_plot_filtered.set_data(x_filt, y_filt)
                self._update_target_marker(filtered_scan, filtered_angles_rad, mode="cartesian")
            else:
                self.lidar_plot_filtered.set_data([], [])
                # Remove persistent target marker if no filtered data is displayed
                if self.target_marker is not None:
                    self.target_marker.remove()
                    self.target_marker = None

            current_mode = "Raw + Filtered" if self.show_filtered else "Raw"
            self.ax.set_title(f"{current_mode} LiDAR (Cartesian) @ {self.timestamps[idx]:.2f}s")
            self.ax.legend()

        if self.fig:
            self.fig.canvas.draw_idle()

    def on_filter_button(self, event):
        """
        Toggles displaying filtered data.
        """
        self.show_filtered = not self.show_filtered
        label = "Filter: ON" if self.show_filtered else "Filter: OFF"
        self.filter_button.label.set_text(label)
        self.update_plot(self.slider.val)

    def on_plot_mode_button(self, event):
        """
        Toggles between polar and cartesian subplots.
        """
        self.show_polar = not self.show_polar
        label = "Plot: Polar" if self.show_polar else "Plot: Cartesian"
        self.mode_button.label.set_text(label)
        # Clear the target marker so it can be re-created
        self.target_marker = None
        self.update_plot(self.slider.val)

    def on_key_press(self, event: KeyEvent):
        """
        Handles keyboard navigation with left/right arrow keys.
        """
        idx = np.argmin(np.abs(self.timestamps - self.slider.val))
        step = -1 if event.key == "left" else 1 if event.key == "right" else 0
        new_idx = np.clip(idx + step, 0, len(self.timestamps) - 1)
        self.slider.set_val(self.timestamps[new_idx])
        self.update_plot(self.timestamps[new_idx])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lidar_plot.py <filename>")
        sys.exit(1)
    try:
        filename = sys.argv[1]
        lidar_vis = LidarVisualizer(filename)
        fig = plt.figure(figsize=(12, 6))
        lidar_vis.add_subplots(fig)
        lidar_vis.enable_slider_and_buttons(fig)
        plt.legend()
        plt.show()
    except FileNotFoundError:
        print(f"File {sys.argv[1]} not found.")