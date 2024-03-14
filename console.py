import os

from typing import Any, List

from datetime import datetime


NORMAL = "\33[0m"
GREEN = "\33[32m"
BLUE  = "\33[34m"
GRAY  = "\33[90m"

UNDERLINE = "\33[4m"

# Header of the CSV log file
HEADER = "timestamp/speed_sensor/rear_distance/battery_voltage/steer/speed/pointcloud\n"


class Console:
    def __init__(self, path: str = "logs") -> None:
        """
        Creates the log file using the code execution timestamp.

        Args:
            path (str, optional): logs folder path. Defaults to "logs".
        """

        timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S.csv")
        self.filename = os.path.join(path, *timestamp.split("/"))

        # Creates the directory and log file
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))

        self.file = open(self.filename, "+a", encoding="utf8")
        self.file.write(HEADER)

        self.counter = 0

        self.info(f"Data stored in {UNDERLINE}{self.filename}{NORMAL}")

    def log(self, data: List[Any]) -> None:
        """
        Appends data to the log file and saves it every 10 new lines.

        Args:
            data (List[Any]): data to be logged in.
        """

        timestamp = datetime.timestamp(datetime.now())
        row = "{}/{}/{}/{}/{}/{}/{}\n".format(timestamp, *data)

        self.file.write(row)
        self.counter += 1

        if self.counter > 10:
            self.file.close()
            self.file = open(self.filename, "+a", encoding="utf8")

            self.counter = 0

    def info(self, message: Any) -> None:
        """
        Displays information on the terminal with its timestamp.

        Args:
            message (Any): message to be displayed on the console.
        """

        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"\r{GREEN}{timestamp} {BLUE}[INFO]{NORMAL} {message}")

    def close(self) -> None:
        """
        Properly closes log file.
        """

        self.file.close()
