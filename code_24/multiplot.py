import sys
import json
import warnings
import numpy as np
import pandas as pd
from datetime import datetime
from matplotlib import pyplot as plt
from matplotlib.widgets import Slider, CheckButtons
from matplotlib.backend_bases import KeyEvent
from control import filter, compute_steer_from_lidar, get_nonzero_points_in_hitbox

#warnings.filterwarnings("ignore")

# Global configuration
WINDOW_SIZE = 8.0  # seconds for the time window around the slider's value
NORMAL = "\33[0m"
GREEN = "\33[32m"
BLUE  = "\33[34m"
UNDERLINE = "\33[4m"

# Matplotlib style
plt.style.use(
    [
        "seaborn-v0_8-whitegrid",
        "seaborn-v0_8-muted",
        {
            "axes.edgecolor": "0.7",
            "axes.labelcolor": "0.2",
            "axes.titlesize": 10,
            "figure.autolayout": True,
            "font.family": ["serif"],
            "grid.linestyle": "--",
            "legend.facecolor": "0.9",
            "legend.frameon": True,
            "savefig.transparent": True
        }
    ]
)

###############################################################################
#                                HELPER FUNCTIONS                             #
###############################################################################

def info(message: str) -> None:
    """
    Displays information on the terminal with its timestamp.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\r{GREEN}{timestamp} {BLUE}[INFO]{NORMAL} {message}")

def read_log(filename: str) -> pd.DataFrame:
    """
    Reads a log file and returns the data as a pandas DataFrame.
    Expects a CSV with '/' as the delimiter and a 'pointcloud' column 
    containing JSON arrays of length 360.

    Args:
        filename (str): The path to the CSV log file.

    Returns:
        pd.DataFrame: The log data.
    """
    df = pd.read_csv(filename, delimiter="/")
    # Convert the 'pointcloud' field from JSON string into a numpy array
    df["pointcloud"] = df["pointcloud"].apply(lambda item: np.asarray(json.loads(item)))
    return df

def lineplot(ax: plt.Axes, x: np.ndarray, y: np.ndarray, **kwargs) -> None:
    """
    Draws a line plot and fills the area under the curve.

    Args:
        ax (plt.Axes): The axes to plot on.
        x (np.ndarray): X-values (timestamps).
        y (np.ndarray): Y-values.
        **kwargs: Additional keyword arguments passed to matplotlib functions.
    """
    fill_style = {"color": "#4878cf", "alpha": 0.2}
    line_style = {"marker": "none", "linestyle": "solid", "color": "#4878cf"}

    # Update with user-provided style if any
    fill_style.update(kwargs)
    line_style.update(kwargs)

    ax.fill_between(x, y, np.zeros_like(x), **fill_style)
    ax.plot(x, y, **line_style)

###############################################################################
#                                   MAIN LOGIC                                #
###############################################################################

def main(filename: str) -> None:
    """
    Main function to visualize the log data along with filtered lidar data.

    Args:
        filename (str): Path to the CSV log file.
    """
    info(f"Reading {UNDERLINE}{filename}{NORMAL}\n")
    df = read_log(filename)

    info("Use arrow keys to change time")
    info("Press CTRL + left/right to take large steps")

    # Prepare timestamps (zero-based time)
    timestamps = df["timestamp"].to_numpy()
    timestamps -= timestamps[0]

    # Precompute angles for converting lidar scan to x-y coordinates
    angles = np.deg2rad(np.arange(0, 360))
    cosines, sines = np.cos(angles), np.sin(angles)

    # Figure and axes (GridSpec for custom layout)
    fig = plt.figure(figsize=(12, 6))
    gs = fig.add_gridspec(4, 3, width_ratios=[2, 1, 1], height_ratios=[1, 1, 2, 0])

    # Axes definitions
    ax_lidar = fig.add_subplot(gs[:3, 0])
    ax_speed = fig.add_subplot(gs[:2, 1])
    ax_steer = fig.add_subplot(gs[:2, 2])
    ax_batt  = fig.add_subplot(gs[2:, 1])
    ax_sonic = fig.add_subplot(gs[2:, 2])

    # Set up each axes
    ax_lidar.set_aspect("equal")
    ax_lidar.set_xlabel("y [m]")
    ax_lidar.set_ylabel("x [m]")
    ax_lidar.set_xlim([  2.50, -2.50])  # reversed x-axis for y [m]
    ax_lidar.set_ylim([ -1.00,  4.00])
    draw_vehicle(ax_lidar)  # draws vehicle shape for reference

    ax_speed.set_title("Speed")
    ax_speed.set_xlabel("t [s]")
    ax_speed.set_ylabel("command [%]")
    ax_speed.set_ylim([-0.08, 1.58])

    ax_steer.set_title("Steer")
    ax_steer.set_xlabel("t [s]")
    ax_steer.set_ylabel("command [deg]")
    ax_steer.set_ylim([-22.00, 22.00])

    ax_batt.set_title("Battery")
    ax_batt.set_xlabel("t [s]")
    ax_batt.set_ylabel("voltage [V]")
    ax_batt.set_ylim([6.40, 8.60])

    ax_sonic.set_title("Ultrasonic")
    ax_sonic.set_xlabel("t [s]")
    ax_sonic.set_ylabel("distance [cm]")
    ax_sonic.set_ylim([-1.50, 31.50])

    # Slider for time navigation
    slider_ax = fig.add_axes([0.065, 0.025, 0.35, 0.03])
    slider = Slider(
        ax=slider_ax,
        label="time",
        valmin=0,
        valmax=timestamps[-1],
        valinit=0,
        valfmt=" %.2f s"
    )

    # Lidar raw data (blue circles)
    lidar_raw_style = {"marker": "o", "linestyle": "none", "color": "#4878cf"}
    lidar_raw, = ax_lidar.plot(np.zeros(360), np.zeros(360), **lidar_raw_style)

    # Lidar filtered data (red circles)
    lidar_filtered_style = {"marker": "o", "linestyle": "none", "color": "#d1022f"}
    lidar_filtered, = ax_lidar.plot(np.zeros(360), np.zeros(360), **lidar_filtered_style)

    # Checkbox to toggle raw vs. filtered lidar visibility
    checkbox_ax = fig.add_axes([0.85, 0.75, 0.1, 0.15])
    labels = ["Raw", "Filtered"]
    visibility = [True, True]  # both on by default
    check = CheckButtons(checkbox_ax, labels, visibility)

    def toggle_visibility(label: str):
        """Toggle visibility of the corresponding lidar layer."""
        if label == "Raw":
            lidar_raw.set_visible(not lidar_raw.get_visible())
        elif label == "Filtered":
            lidar_filtered.set_visible(not lidar_filtered.get_visible())
        fig.canvas.draw_idle()

    check.on_clicked(toggle_visibility)

    # Time-series plots on ax_speed, ax_steer, ax_batt, ax_sonic
    lineplot(ax_speed, timestamps, df["speed"].to_numpy())
    lineplot(ax_steer, timestamps, df["steer"].to_numpy())
    lineplot(ax_batt,  timestamps, df["battery_voltage"].to_numpy())
    lineplot(ax_sonic, timestamps, df["rear_distance"].to_numpy())

    # Add an additional trace to speed axis: speed_sensor (normalized)
    speed_sensor = df["speed_sensor"].to_numpy()
    speed_sensor_norm = speed_sensor / np.max(speed_sensor[speed_sensor < 5.0])
    ax_speed.plot(timestamps, speed_sensor_norm, 
                  linestyle="solid", color="#0d3b85", label="sensor")
    ax_speed.legend(loc="lower right")

    # Vertical lines (dashed) that move with the slider on each axis
    vlines_style = {"marker": "none", "linestyle": "dashed", "color": "#d1022f"}
    vlines = []
    for ax in (ax_speed, ax_steer, ax_batt, ax_sonic):
        line, = ax.plot([0.0, 0.0], [-40.0, 40.0], **vlines_style)
        vlines.append(line)

    hitbox_scatter = None
    target_line = None

    def update_plot(value: float) -> None:
        """
        Updates all plots (lidar + time-series vertical lines) based on slider value.

        Args:
            value (float): The current time (in seconds) from the slider.
        """
        # Find closest index in the DataFrame to the chosen time
        idx = np.argmin(np.abs(timestamps - value))
        data = df.iloc[idx]

        # Raw lidar conversion (polar to Cartesian)
        raw_scan = data["pointcloud"]
        lidar_raw.set_xdata(-raw_scan * sines)
        lidar_raw.set_ydata( raw_scan * cosines)

        # Filtered lidar
        scan_dist, scan_angle = filter(raw_scan)
        steer, steer_dc, target_angle = compute_steer_from_lidar(raw_scan)
        print(steer, steer_dc, target_angle)

        lidar_filtered.set_xdata(-scan_dist * sines[scan_angle])
        lidar_filtered.set_ydata( scan_dist * cosines[scan_angle])

        
        

        target_angle_rad = np.deg2rad(target_angle)
        # Use the converted angle for interpolation and coordinate conversion.
        target_distance = np.interp(target_angle_rad, scan_angle, scan_dist)

        target_x =  -target_distance * np.sin(target_angle_rad)
        target_y =  target_distance * np.cos(target_angle_rad)
        
        nonlocal target_line
        if target_line is None:
            # Create the target line (dashed red line)
            target_line, = ax_lidar.plot([0, target_x], [0, target_y], 'g--', lw=2, label="Target")
        else:
            # Update the target line coordinates
            target_line.set_data([0, target_x], [0, target_y])

        # Nonzero points in "hitbox"
        nonzero_x, nonzero_y = get_nonzero_points_in_hitbox(raw_scan)
        
        nonlocal hitbox_scatter
        if hitbox_scatter is None:
            # Create the scatter if it doesn't exist
            hitbox_scatter = ax_lidar.scatter(nonzero_x, nonzero_y, 
                                              c="yellow", s=30, zorder=3, 
                                              label="Hitbox Points")
        else:
            # Update existing scatter
            hitbox_scatter.set_offsets(np.column_stack((nonzero_x, nonzero_y)))

        # Move vertical lines in time-series plots
        for line in vlines:
            line.set_xdata([value, value])

        # Adjust time window for better zoom
        if timestamps[-1] <= WINDOW_SIZE:
            # If your entire timeline is smaller than the window, show it all
            start_time = timestamps[0]
            end_time   = timestamps[-1]
        else:
            # Keep a window around the slider's value
            half_win = 0.5 * WINDOW_SIZE
            # Bound the window so it doesn't exceed the data range
            value_adj = max(value, timestamps[0] + half_win)
            value_adj = min(value_adj, timestamps[-1] - half_win)
            start_time = value_adj - half_win
            end_time   = value_adj + half_win

        # Apply new limits to all time-series subplots
        margin = 0.05 * WINDOW_SIZE
        for ax in (ax_speed, ax_steer, ax_batt, ax_sonic):
            ax.set_xlim([start_time - margin, end_time + margin])

        fig.canvas.draw_idle()

    def on_key_press(event: KeyEvent) -> None:
        """
        Keyboard event handler for stepping through time with arrow keys.
        Press 'ctrl+left' or 'ctrl+right' for larger steps.

        Args:
            event (KeyEvent): The key event captured by matplotlib.
        """
        # Find current index based on slider's value
        idx = np.argmin(np.abs(timestamps - slider.val))
        step = 1  # normal step
        if event.key == "ctrl+left":
            step = -10
        elif event.key == "ctrl+right":
            step = 10
        elif event.key == "left":
            step = -1
        elif event.key == "right":
            step = 1
        else:
            # Do nothing if it's not one of the recognized keys
            return

        new_idx = np.clip(idx + step, 0, len(timestamps) - 1)
        new_time = timestamps[new_idx]
        slider.set_val(new_time)  # this triggers update_plot
        update_plot(new_time)

    # Initialize at time = 0.0
    update_plot(0.0)
    slider.on_changed(update_plot)
    fig.canvas.mpl_connect("key_press_event", on_key_press)

    # Adjust layout
    plt.subplots_adjust(
        top=0.944,
        bottom=0.088,
        left=0.021,
        right=0.988,
        hspace=0.953,
        wspace=0.2
    )
    plt.show()

def draw_vehicle(ax: plt.Axes) -> None:
    """
    Draws a schematic of the vehicle on the provided Axes.

    Args:
        ax (plt.Axes): The axes on which to draw the vehicle.
    """
    # Body shape
    vehicle = np.array(
        [[ 0.00000000,  0.0951087 ],
         [ 0.07500000,  0.09103261],
         [ 0.09103261,  0.06059783],
         [ 0.09728261,  0.03668478],
         [ 0.09836957,  0.01385870],
         [ 0.09483696, -0.00760870],
         [ 0.08994565, -0.02771739],
         [ 0.08614130, -0.03043478],
         [ 0.08913043, -0.06277174],
         [ 0.08614130, -0.06168478],
         [ 0.08396739, -0.14782609],
         [ 0.08994565, -0.20163043],
         [ 0.08940217, -0.24972826],
         [ 0.08070652, -0.28451087],
         [ 0.07418478, -0.29347826],
         [ 0.07065217, -0.31222826],
         [ 0.00000000, -0.31630435]]
    )
    # Mirror the right side for a symmetrical shape
    mirrored = np.copy(vehicle)
    mirrored[:, 0] = -mirrored[:, 0]
    mirrored = mirrored[::-1]
    vehicle = np.append(vehicle, mirrored, axis=0)

    # Body styling
    ax.fill(vehicle[:, 0], vehicle[:, 1], color="#0d3b85", zorder=100)

    # Glass (windshield)
    glass = np.array(
        [[ 0.02173913, -0.01494565],
         [ 0.07364130, -0.03070652],
         [ 0.05461957, -0.07989130],
         [-0.05461957, -0.07989130],
         [-0.07364130, -0.03070652],
         [-0.02173913, -0.01494565],
         [ 0.02173913, -0.01494565]]
    )
    ax.fill(glass[:, 0], glass[:, 1], color="#ffffff", zorder=101)

###############################################################################
#                                  ENTRY POINT                                #
###############################################################################

if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Log file not specified. Usage: python plot_log.py <log_file.csv>")
        sys.exit(1)

    try:
        main(filename)
    except FileNotFoundError:
        info(f"{UNDERLINE}{filename}{NORMAL} not found")