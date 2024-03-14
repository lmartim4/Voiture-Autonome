import sys
import json

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt


def read_log(filename: str) -> pd.DataFrame:
    df = pd.read_csv(filename, delimiter="/")

    # Parse string to array
    df["pointcloud"] = df["pointcloud"].apply(
        lambda item: np.asarray(json.loads(item)))

    return df


def show_map(df: pd.DataFrame) -> None:
    angles = np.linspace(0, 2 * np.pi, 360)

    fig, ax = plt.subplots()
    ax.set_aspect("equal")

    for distances in df["pointcloud"].to_numpy():
        x = -distances * np.cos(angles)
        y =  distances * np.sin(angles)

        points = np.concatenate(
            (x[:, np.newaxis], y[:, np.newaxis]), axis=1)

        ax.plot(points[:, 0], points[:, 1], "bo")

    plt.tight_layout()
    # plt.savefig("image.png")
    plt.show()


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = "logs/2024-03-13/02-03-44.csv"

    try:
        print(f"Reading {filename}")
        show_map(read_log(filename))
    except FileNotFoundError:
        print(f"{filename} not found")
