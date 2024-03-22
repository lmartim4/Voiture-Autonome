import sys

import json

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt
from matplotlib.widgets import Slider


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


def read_log(filename: str) -> pd.DataFrame:
    df = pd.read_csv(filename, delimiter="/")

    # Parse string to array
    df["pointcloud"] = df["pointcloud"].apply(
        lambda item: np.asarray(json.loads(item)))

    return df


def draw_vehicle(ax) -> None:
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
    df = read_log(filename)

    timestamps = df["timestamp"].to_numpy()
    timestamps -= timestamps[0]

    scale = (len(timestamps) - 1) / timestamps[-1]

    angles = np.linspace(0, 2 * np.pi, 360)
    cos, sin = np.cos(angles), np.sin(angles)

    points = np.zeros((0, 2))

    for distances in df["pointcloud"].to_numpy():
        x = -distances * cos
        y =  distances * sin

        tmp = np.concatenate(
            (x[:, np.newaxis], y[:, np.newaxis]), axis=1)

        points = np.append(points, tmp, axis=0)

        del tmp

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

    ax1.set_xlabel("x [m]")
    ax1.set_ylabel("y [m]")

    for ax in [ax2, ax3, ax4, ax5]:
        ax.set_xlabel("t [s]")

    ax2.set_ylabel("command [%]")
    ax3.set_ylabel("command [deg]")
    ax4.set_ylabel("voltage [V]")
    ax5.set_ylabel("distance [cm]")

    ax1.set_xlim([ -2.50,  2.50])
    ax1.set_ylim([ -1.00,  4.00])
    ax2.set_ylim([ -0.05,  1.05])
    ax3.set_ylim([-18.90, 18.90])
    ax4.set_ylim([  4.68,  7.32])
    ax5.set_ylim([  0.00, 31.50])

    slider = Slider(
        ax=fig.add_axes([0.065, 0.025, 0.35, 0.03]),
        label="time",
        valmin=0,
        valmax=timestamps[-1],
        valinit=0,
        valfmt="%.2f s"
    )

    style = {"marker": "o", "linestyle": "none", "color": "#4878cf"}
    lidar, = ax1.plot(points[:, 0], points[:, 1], **style)

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
        index = int(scale * value)

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
        filename = "00-19-17.csv"

    try:
        print(f"Reading {filename}")
        main(filename)
    except FileNotFoundError:
        print(f"{filename} not found")
