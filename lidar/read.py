import json

import numpy as np
import pandas as pd


def read_log(filename: str) -> pd.DataFrame:
    df = pd.read_csv(filename, delimiter="/")

    # Parse string to array
    df["pointcloud"] = df["pointcloud"].apply(
        lambda item: np.asarray(json.loads(item)))

    return df


if __name__ == "__main__":
    print(read_log("logs/2024-02-04/16-22-53.csv"))
