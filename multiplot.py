import sys

import json

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt
from matplotlib.widgets import Slider


def read_log(filename: str) -> pd.DataFrame:
    df = pd.read_csv(filename, delimiter="/")

    # Parse string to array
    df["pointcloud"] = df["pointcloud"].apply(
        lambda item: np.asarray(json.loads(item)))

    return df


def main(filename: str) -> None:
    df = read_log(filename)

    timestamps = df["timestamp"].to_numpy()
    ini_time = timestamps[ 0]
    end_time = timestamps[-1]

    factor = (len(timestamps) - 1) / (end_time - ini_time)

    angles = np.linspace(0, 2 * np.pi, 360)
    cos, sin = np.cos(angles), np.sin(angles)

    points = np.zeros((0, 2))

    for distances in df["pointcloud"].to_numpy():
        x = -distances * cos
        y =  distances * sin

        tmp = np.concatenate(
            (x[:, np.newaxis], y[:, np.newaxis]), axis=1)

        points = np.append(points, tmp, axis=0)

    fig = plt.figure(figsize=(12, 6))

    gs = fig.add_gridspec(
        4, 3, width_ratios=[2, 1, 1], height_ratios=[0.755, 0.755, 1.49, 0.02])

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

    ax1.set_xlabel("x [m]")
    ax1.set_ylabel("y [m]")

    ax2.set_xlabel("t [s]")
    ax2.set_ylabel("command [%]")

    ax3.set_xlabel("t [s]")
    ax3.set_ylabel("command [deg]")

    ax4.set_xlabel("t [s]")
    ax4.set_ylabel("voltage [V]")

    ax5.set_xlabel("t [s]")
    ax5.set_ylabel("distance [cm]")

    ax2.set_ylim([  0.0,  1.0])
    ax3.set_ylim([-18.0, 18.0])
    ax4.set_ylim([  0.0,  7.2])
    ax5.set_ylim([  0.0, 10.0])

    slider = Slider(
        ax=fig.add_axes([0.065, 0.025, 0.35, 0.03]),
        label="time",
        valmin=0,
        valmax=end_time - ini_time,
        valinit=0,
        valfmt="%.2f s"
    )

    lidar, = ax1.plot(points[:, 0], points[:, 1], "bo")
    ax2.plot(timestamps - ini_time, df["speed"].to_numpy(), "b-")
    ax3.plot(timestamps - ini_time, df["steer"].to_numpy(), "b-")
    ax4.plot(timestamps - ini_time, df["speed"].to_numpy(), "b-")
    ax5.plot(timestamps - ini_time, df["steer"].to_numpy(), "b-")

    lines = []
    for ax in [ax2, ax3, ax4, ax5]:
        tmp, = ax.plot([0.0, 0.0], [-20.0, 20.0], "r--")
        lines.append(tmp)

    def update(value: float) -> None:
        index = int(factor * value)

        if index == 0:
            lidar.set_xdata(points[:, 0])
            lidar.set_ydata(points[:, 1])

        else:
            data = df.iloc[index]

            lidar.set_xdata(-data["pointcloud"] * cos)
            lidar.set_ydata( data["pointcloud"] * sin)

        for line in lines:
            line.set_xdata([value, value])

        fig.canvas.draw_idle()

    slider.on_changed(update)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = "05-39-51.csv"

    try:
        print(f"Reading {filename}")
        main(filename)
    except FileNotFoundError:
        print(f"{filename} not found")
