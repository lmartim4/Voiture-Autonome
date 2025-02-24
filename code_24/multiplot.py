import os
import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
import constants
import matplotlib.pyplot as plt
from plot_algorithm import AlgorithmViewer

today = datetime.date.today().strftime("%Y-%m-%d")
logs_dir = os.path.join(os.path.dirname(__file__), "../logs/", today)

root = tk.Tk()
root.withdraw()

logfile_path = filedialog.askopenfilename(
    initialdir=logs_dir,
    title="Select Log File",
    filetypes=(("log files", "*.log"), ("all files", "*.*"))
)

if not logfile_path:
    print("No log file selected. Exiting.")
    exit(0)

logfile_dir = os.path.dirname(logfile_path)
backup_path = os.path.join(logfile_dir, "config.json")

if os.path.isfile(backup_path):
    use_backup = messagebox.askyesno(
        "Load Configuration",
        "config.json found.\nDo you want to load backed-up constants?\n"
        "Click 'Yes' for backup constants or 'No' for current config."
    )
    if use_backup:
        constants.load_constants(backup_path)
        print("Loaded backed-up configuration.")
    else:
        print("No config.json file found in the log directory. Loading current configuration.")
    pass

lidar_vis = AlgorithmViewer(logfile_path)

fig, axs = plt.subplots(1, 1, figsize=(20, 20), subplot_kw={'projection': 'polar'})

lidar_vis.add_subplot(axs)
lidar_vis.enable_slider_and_buttons(fig)

plt.show()
