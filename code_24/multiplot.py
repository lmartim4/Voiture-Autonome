import os
import sys
import json
import datetime
import tkinter as tk
import pandas as pd
import numpy as np
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# Local modules
import constants
from algorithm_visualizer import VoitureAlgorithmPlotter


def read_lidar_log(filename: str) -> pd.DataFrame:
    """
    Reads a LiDAR log file and returns a DataFrame with the columns:
        - timestamp
        - pointcloud (as a NumPy array)
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

            timestamp_str, array_str = split_line
            try:
                # Convert from milliseconds to seconds
                timestamp_val = float(timestamp_str) / 1000.0
                pointcloud = np.array(json.loads(array_str), dtype=float)

                # Basic validation
                if len(pointcloud) != 360:
                    print(f"Warning: Invalid pointcloud length: {len(pointcloud)}")

                records.append({"timestamp": timestamp_val, "pointcloud": pointcloud})
            except Exception as e:
                print(f"Error parsing line: {line}\n{e}")

    return pd.DataFrame(records)


def parse_arguments() -> str:
    """
    Parses command line arguments and returns the logfile path if provided.
    Otherwise, returns None.
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    return None


def select_log_file() -> str:
    """
    Opens a file dialog to select a log file from today's directory (by default).
    Returns the selected logfile path, or None if none is selected.
    """
    today = datetime.date.today().strftime("%Y-%m-%d")
    default_logs_dir = os.path.join(os.path.dirname(__file__), "../logs/", today)

    root = tk.Tk()
    root.withdraw()

    logfile_path = filedialog.askopenfilename(
        initialdir=default_logs_dir,
        title="Select Log File",
        filetypes=(("log files", "*.log"), ("all files", "*.*"))
    )

    if not logfile_path:
        print("No log file selected. Exiting.")
        return None

    return logfile_path


def load_backup_constants(logfile_dir: str) -> None:
    """
    Checks if there's a config.json in the given directory. If found, prompts user
    whether to load that config or retain current constants. Updates constants if user agrees.
    """
    backup_path = os.path.join(logfile_dir, "config.json")
    if os.path.isfile(backup_path):
        use_backup = messagebox.askyesno(
            "Load Configuration",
            ("config.json found.\n"
             "Do you want to load backed-up constants?\n"
             "Click 'Yes' for backup constants or 'No' for current config.")
        )
        if use_backup:
            constants.load_constants(backup_path)
            print("Loaded backed-up configuration.")
        else:
            print("Using current configuration.")
    else:
        print("No config.json file found in the log directory. Using current configuration.")


def update_plot(val, data: pd.DataFrame, slider: Slider, vis: VoitureAlgorithmPlotter):
    """
    Called whenever the slider value changes. Retrieves the corresponding pointcloud
    for the chosen timestamp and updates the plot.
    """
    timestamp = slider.val
    # Retrieve pointcloud corresponding to the selected timestamp
    matching_rows = data.loc[data["timestamp"] == timestamp, "pointcloud"]
    if not matching_rows.empty:
        pointcloud = matching_rows.values[0]
        vis.updateView(pointcloud)


def main():
    # 1. Parse CLI arguments or prompt user for a logfile path
    logfile_path = parse_arguments()
    if logfile_path is None:
        logfile_path = select_log_file()
        if not logfile_path:
            sys.exit(0)

    # 2. Possibly load backup constants if config.json exists
    logfile_dir = os.path.dirname(logfile_path)
    load_backup_constants(logfile_dir)

    # 3. Read the LiDAR log data
    data = read_lidar_log(logfile_path)
    if data.empty:
        print("No valid data found in the log file.")
        sys.exit(1)

    # 4. Initialize the plotting tool
    vis = VoitureAlgorithmPlotter()

    # 5. Create a slider for timestamps
    slider_ax = vis.fig.add_axes([0.2, 0.02, 0.6, 0.03])
    timestamps = data["timestamp"].values

    slider = Slider(
        ax=slider_ax,
        label="Time (s)",
        valmin=timestamps[0],
        valmax=timestamps[-1],
        valinit=timestamps[0],
        valfmt="%.2f s",
        valstep=timestamps  # ensures the slider steps exactly to each timestamp
    )

    # 6. Register a callback for slider changes (use lambda or partial for additional args)
    slider.on_changed(lambda val: update_plot(val, data, slider, vis))

    # 7. Initialize the view with the second record (or first, but ensure it exists)
    initial_index = 1 if len(data) > 1 else 0
    vis.updateView(data["pointcloud"].iloc[initial_index])

    # 8. Show the plot
    plt.show()


if __name__ == "__main__":
    main()