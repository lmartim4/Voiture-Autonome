import sys

import json

import warnings

import numpy as np
import pandas as pd

from datetime import datetime

from matplotlib import pyplot as plt
from matplotlib.widgets import Slider

from matplotlib.backend_bases import KeyEvent

from constants import *


WINDOW_SIZE = 8.0  # Seconds

NORMAL = "\33[0m"
GREEN = "\33[32m"
BLUE  = "\33[34m"

UNDERLINE = "\33[4m"


warnings.filterwarnings("ignore")

plt.style.use(
    ["seaborn-v0_8-whitegrid", "seaborn-v0_8-muted", {
        "axes.edgecolor": "0.7",
        "axes.labelcolor": "0.2",
        "axes.titlesize": 10,
        "figure.autolayout": True,
        "font.family": ["serif"],
        "grid.linestyle": "--",
        "legend.facecolor": "0.9",
        "legend.frameon": True,
        "savefig.transparent": True
    }]
)


def info(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")

    print(f"\r{GREEN}{timestamp} {BLUE}[INFO]{NORMAL} {message}")


def read_log(filename: str) -> pd.DataFrame:
    df = pd.read_csv(filename, delimiter="/")

    # Parse string to array
    df["pointcloud"] = df["pointcloud"].apply(
        lambda item: np.asarray(json.loads(item)))

    return df


def draw_vehicle(ax: plt.Axes) -> None:
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

    tmp = np.copy(vehicle)
    tmp[:, 0] = -tmp[:, 0]
    tmp = tmp[::-1]

    vehicle = np.append(vehicle, tmp, axis=0)

    del tmp

    style = {"color": "#0d3b85", "zorder": 100}
    ax.fill(vehicle[:, 0], vehicle[:, 1], **style)

    glass = np.array(
        [[ 0.02173913, -0.01494565],
         [ 0.07364130, -0.03070652],
         [ 0.05461957, -0.07989130],
         [-0.05461957, -0.07989130],
         [-0.07364130, -0.03070652],
         [-0.02173913, -0.01494565],
         [ 0.02173913, -0.01494565]]
    )

    style = {"color": "#ffffff", "zorder": 101}
    ax.fill(glass[:, 0], glass[:, 1], **style)


def main(filename: str) -> None:
    info(f"Reading {UNDERLINE}{filename}{NORMAL}\n")

    df = read_log(filename)

    info("Use arrow keys to change time")
    info("Press CTRL to take large steps")

    timestamps = df["timestamp"].to_numpy()
    timestamps -= timestamps[0]

    angles = np.deg2rad(np.arange(0, 360) - LIDAR_HEADING)
    cos, sin = np.cos(angles), np.sin(angles)

    fig = plt.figure(figsize=(12, 6))

    gs = fig.add_gridspec(
        4, 3, width_ratios=[2, 1, 1], height_ratios=[1, 1, 2, 0])

    ax1 = fig.add_subplot(gs[:3, 0])
    ax2 = fig.add_subplot(gs[:2, 1])
    ax3 = fig.add_subplot(gs[:2, 2])
    ax4 = fig.add_subplot(gs[2:, 1])
    ax5 = fig.add_subplot(gs[2:, 2])

    ax1.set_aspect("equal")

    ax2.set_title("speed")
    ax3.set_title("steer")
    ax4.set_title("battery")
    ax5.set_title("ultrassonic")

    ax1.set_xlabel("y [m]")
    ax1.set_ylabel("x [m]")

    for ax in [ax2, ax3, ax4, ax5]:
        ax.set_xlabel("t [s]")

    ax2.set_ylabel("command [%]")
    ax3.set_ylabel("command [deg]")
    ax4.set_ylabel("voltage [V]")
    ax5.set_ylabel("distance [cm]")

    ax1.set_xlim([  2.50, -2.50])
    ax1.set_ylim([ -1.00,  4.00])
    ax2.set_ylim([ -0.05,  1.05])
    ax3.set_ylim([-22.00, 22.00])
    ax4.set_ylim([  6.95,  8.05])
    ax5.set_ylim([ -1.50, 31.50])

    slider = Slider(
        ax=fig.add_axes([0.065, 0.025, 0.35, 0.03]),
        label="time",
        valmin=0,
        valmax=timestamps[-1],
        valinit=0,
        valfmt=" %.2f s"
    )

    style = {"marker": "o", "linestyle": "none", "color": "#4878cf"}
    lidar, = ax1.plot(np.zeros(360), np.zeros(360), **style)

    draw_vehicle(ax1)


    def lineplot(ax: plt.Axes, x: np.ndarray, y: np.ndarray) -> None:
        style = {"color": "#4878cf", "alpha": 0.2}
        ax.fill_between(x=x, y1=y, y2=np.zeros(np.shape(x)), **style)

        style = {"marker": "none", "linestyle": "solid", "color": "#4878cf"}
        ax.plot(x, y, **style)


    lineplot(ax2, timestamps, df["speed"].to_numpy())
    lineplot(ax3, timestamps, df["steer"].to_numpy())
    lineplot(ax4, timestamps, df["battery_voltage"].to_numpy())
    lineplot(ax5, timestamps, df["rear_distance"].to_numpy())

    tmp = df["speed_sensor"].to_numpy()
    tmp = tmp / np.max(tmp[tmp < 5.0])

    style = {"marker": "none", "linestyle": "solid", "color": "#0d3b85"}
    ax2.plot(timestamps, tmp, label="sensor", **style)
    ax2.legend(loc="lower right")

    del tmp

    style = {"marker": "none", "linestyle": "dashed", "color": "#d1022f"}

    lines = []
    for ax in [ax2, ax3, ax4, ax5]:
        tmp, = ax.plot([0.0, 0.0], [-40.0, 40.0], **style)
        lines.append(tmp)

        del tmp


    def update(value: float) -> None:
        index = np.argmin(np.abs(timestamps - value))

        data = df.iloc[index]

        lidar.set_xdata(-data["pointcloud"] * sin)
        lidar.set_ydata( data["pointcloud"] * cos)

        for line in lines:
            line.set_xdata([value, value])

        if timestamps[-1] <= WINDOW_SIZE:
            ini_timestamp = timestamps[ 0]
            end_timestamp = timestamps[-1]

        else:
            value = max(value, timestamps[ 0] + 0.5 * WINDOW_SIZE)
            value = min(value, timestamps[-1] - 0.5 * WINDOW_SIZE)

            ini_timestamp = value - 0.5 * WINDOW_SIZE
            end_timestamp = value + 0.5 * WINDOW_SIZE

        for ax in [ax2, ax3, ax4, ax5]:
            ax.set_xlim(
                [ini_timestamp - 0.05 * WINDOW_SIZE,
                 end_timestamp + 0.05 * WINDOW_SIZE]
            )

        fig.canvas.draw_idle()


    def on_press(event: KeyEvent) -> None:
        index = np.argmin(np.abs(timestamps - slider.val))

        if event.key == "left":
            index -= 1
        if event.key == "right":
            index += 1

        if event.key == "ctrl+left":
            index -= 10
        if event.key == "ctrl+right":
            index += 10

        index = np.clip(index, 0, len(timestamps) - 1)

        slider.set_val(timestamps[index])

        update(timestamps[index])


    update(0.0)

    slider.on_changed(update)

    fig.canvas.mpl_connect("key_press_event", on_press)

    plt.subplots_adjust(
        top=0.944,
        bottom=0.088,
        left=0.021,
        right=0.988,
        hspace=0.953,
        wspace=0.2
    )

    plt.show()


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = "logs/18-30-17.csv"

    try:
        main(filename)
    except FileNotFoundError:
        info(f"{UNDERLINE}{filename}{NORMAL} not found")
