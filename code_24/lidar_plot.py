import sys
import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.backend_bases import KeyEvent
from typing import Tuple
from control import convolution_filter  # Assuming you have this custom function

warnings.filterwarnings("ignore")
plt.style.use(["seaborn-v0_8-whitegrid", "seaborn-v0_8-muted"])

class LidarVisualizer:
    def __init__(self, filename=None, df=None):
        """
        Initializes the LiDAR visualizer.

        Args:
            filename (str, optional): Path to the LiDAR log file.
            df (pd.DataFrame, optional): Preloaded DataFrame with LiDAR data.
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

        # Figure-related
        self.fig = None
        self.ax = None

        # Interactivity
        self.slider = None
        self.filter_button = None
        self.mode_button = None

        # Toggle states
        self.show_filtered = False  # Raw vs. Filtered
        self.show_polar = True      # Polar vs. Cartesian (Initial mode is Polar)

        # Plot line objects (we will create them after the axes exist)
        self.lidar_plot_raw = None
        self.lidar_plot_filtered = None

    @staticmethod
    def read_lidar_log(filename: str) -> pd.DataFrame:
        """
        Reads a LiDAR log file.

        Args:
            filename (str): Path to the log file.

        Returns:
            pd.DataFrame with columns ['timestamp', 'pointcloud'].
        """
        records = []
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue  # Skip empty lines

                split_line = line.split(maxsplit=1)
                if len(split_line) < 2:
                    continue  # Skip invalid lines

                timestamp_str, array_str = split_line[0], split_line[1]
                timestamp = float(timestamp_str)

                try:
                    pointcloud = np.array(json.loads(array_str))  # Parse JSON
                    if len(pointcloud) != 360:
                        continue  # Ensure proper LiDAR format
                    records.append({"timestamp": timestamp, "pointcloud": pointcloud})
                except Exception as e:
                    print(f"Error parsing line: {line}\n{e}")

        return pd.DataFrame(records)

    def add_subplots(self, fig: plt.Figure):
        """
        Create and configure a single subplot, initially polar.
        """
        self.fig = fig

        # Create a single subplot, initially as polar projection
        self.ax = fig.add_subplot(1, 1, 1, projection='polar')
        max_range = self.df["pointcloud"].apply(lambda x: max(x)).max()

        # Create line objects for the plot
        self.lidar_plot_raw, = self.ax.plot([], [], 'bo', markersize=3, label="Raw LiDAR")
        self.lidar_plot_filtered, = self.ax.plot([], [], 'ro', markersize=3, label="Filtered LiDAR")

        # Initialize with the first timestamp data, in polar mode initially
        self.update_plot(self.timestamps[0])

    def add_subplot(self, ax: plt.Axes):
        """
        Accepts an existing Axes (for example, from a multiplot layout) and 
        initializes it for LiDAR plotting.
        """
        self.fig = ax.figure
        self.ax = ax
        max_range = self.df["pointcloud"].apply(lambda x: max(x)).max()
        self.lidar_plot_raw, = self.ax.plot([], [], 'bo', markersize=3, label="Raw LiDAR")
        self.lidar_plot_filtered, = self.ax.plot([], [], 'ro', markersize=3, label="Filtered LiDAR")
        self.update_plot(self.timestamps[0])

    def enable_slider_and_buttons(self, fig):
        """
        Adds a time slider, filter toggle button, and plot mode button for user interaction.
        """
        self.fig = fig

        # Slider
        slider_ax = fig.add_axes([0.2, 0.02, 0.6, 0.03])
        self.slider = Slider(
            ax=slider_ax,
            label="Time (s)",
            valmin=0,
            valmax=self.timestamps[-1],
            valinit=0,
            valfmt="%.2f s"
        )
        self.slider.on_changed(self.update_plot)

        # Filter Button
        button_ax = fig.add_axes([0.81, 0.92, 0.1, 0.04])
        self.filter_button = Button(button_ax, "Filter: OFF", color="lightgoldenrodyellow")
        self.filter_button.on_clicked(self.on_filter_button)

        # Plot Mode Button (Polar <-> Cartesian)
        mode_ax = fig.add_axes([0.68, 0.92, 0.1, 0.04])
        mode_label = "Plot: Polar"
        self.mode_button = Button(mode_ax, mode_label, color="lightblue")
        self.mode_button.on_clicked(self.on_plot_mode_button)

        # Keyboard navigation (left/right arrow)
        fig.canvas.mpl_connect("key_press_event", self.on_key_press)

    def enable_slider(self, fig: plt.Figure):
        """
        Adds only a time slider to the figure. This is useful when you already have
        a multiplot layout and want to control one of the subplots.
        """
        self.fig = fig
        slider_ax = fig.add_axes([0.2, 0.02, 0.6, 0.03])
        self.slider = Slider(
            ax=slider_ax,
            label="Time (s)",
            valmin=0,
            valmax=self.timestamps[-1],
            valinit=0,
            valfmt="%.2f s"
        )
        self.slider.on_changed(self.update_plot)

    def update_plot(self, value: float):
        """
        Updates the plot (polar or cartesian) based on the selected time and mode.
        Args:
            value (float): Time value (in seconds) from the slider.
        """
        idx = np.argmin(np.abs(self.timestamps - value))  # Find closest timestamp
        raw_scan = self.df.iloc[idx]["pointcloud"]

        if self.show_polar:
            # -----------------------
            # Update the Plot in Polar Mode
            # -----------------------
            if not hasattr(self.ax, 'set_theta_zero_location'):
                # Save original axes position in the subplot grid
                bbox = self.ax.get_position()
                self.fig.delaxes(self.ax)
                self.ax = self.fig.add_axes(bbox, projection='polar')
                self.lidar_plot_raw, = self.ax.plot([], [], 'bo', markersize=3, label="Raw LiDAR")
                self.lidar_plot_filtered, = self.ax.plot([], [], 'ro', markersize=3, label="Filtered LiDAR")
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
            else:
                self.lidar_plot_filtered.set_data([], [])
                
            self.ax.set_ylim([0, max(raw_scan) * 1.2])
            current_mode = "Raw + Filtered" if self.show_filtered else "Raw"
            self.ax.set_title(f"{current_mode} LiDAR (Polar) @ {self.timestamps[idx]:.2f}s")
            self.ax.legend()

        else:
            # -------------------------
            # Update the Plot in Cartesian Mode
            # -------------------------
            if hasattr(self.ax, 'set_theta_zero_location'):
                bbox = self.ax.get_position()
                self.fig.delaxes(self.ax)
                self.ax = self.fig.add_axes(bbox)
                self.lidar_plot_raw, = self.ax.plot([], [], 'bo', markersize=3, label="Raw LiDAR")
                self.lidar_plot_filtered, = self.ax.plot([], [], 'ro', markersize=3, label="Filtered LiDAR")

            self.ax.set_aspect('equal', adjustable='box')
            max_range = self.df["pointcloud"].apply(lambda x: max(x)).max()
            self.ax.set_xlim([-max_range * 1.2, max_range * 1.2])
            self.ax.set_ylim([-max_range * 1.2, max_range * 1.2])
            self.ax.grid(True)

            x_raw = raw_scan * np.sin(self.angles)
            y_raw = raw_scan * np.cos(self.angles)
            self.lidar_plot_raw.set_data(x_raw, y_raw)

            if self.show_filtered:
                filtered_scan, filtered_angles = convolution_filter(raw_scan)
                filtered_angles_rad = np.radians(filtered_angles)
                x_filt = filtered_scan * np.sin(filtered_angles_rad)
                y_filt = filtered_scan * np.cos(filtered_angles_rad)
                self.lidar_plot_filtered.set_data(x_filt, y_filt)
            else:
                self.lidar_plot_filtered.set_data([], [])

            current_mode = "Raw + Filtered" if self.show_filtered else "Raw"
            self.ax.set_title(f"{current_mode} LiDAR (Cartesian) @ {self.timestamps[idx]:.2f}s")
            self.ax.legend()

        if self.fig:
            self.fig.canvas.draw_idle()

    def on_filter_button(self, event):
        """
        Toggles the display of filtered data.
        """
        self.show_filtered = not self.show_filtered
        label = "Filter: ON" if self.show_filtered else "Filter: OFF"
        self.filter_button.label.set_text(label)
        self.update_plot(self.slider.val)

    def on_plot_mode_button(self, event):
        """
        Toggles between Polar and Cartesian subplots.
        """
        self.show_polar = not self.show_polar
        label = "Plot: Polar" if self.show_polar else "Plot: Cartesian"
        self.mode_button.label.set_text(label)
        if self.show_polar:
            self.ax.set_title("LiDAR Scan (Polar)")
        else:
            self.ax.set_title("LiDAR Scan (Cartesian)")
        self.update_plot(self.slider.val)

    def on_key_press(self, event: KeyEvent):
        """
        Handles keyboard navigation with left/right arrows.
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