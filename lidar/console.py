import os

from typing import Any, List

from datetime import datetime


NORMAL = "\33[0m"
GREEN = "\33[32m"
BLUE  = "\33[34m"
GRAY  = "\33[90m"

UNDERLINE = "\33[4m"

# Header of the CSV log file
HEADER = "timestamp/pointcloud/steer/speed\n"


class Console:
    def __init__(self, path: str = "logs") -> None:
        """
        Creates the log file using the code execution timestamp.

        Args:
            path (str, optional): logs folder path. Defaults to "logs".
        """

        os.system("clear")

        timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S.csv")
        self.filename = os.path.join(path, *timestamp.split("/"))

        # Creates the directory and log file
        if not os.path.exists(os.path.dirname(self.filename)):
            os.makedirs(os.path.dirname(self.filename))

        self.log_file = open(self.filename, "+a", encoding="utf8")
        self.log_file.write(HEADER)

        self.counter = 0

        self.info(f"Data stored in {UNDERLINE}{self.filename}{NORMAL}")

    def log(self, data: List[Any]) -> None:
        """
        Appends data to the log file and saves it every 10 new lines.

        Args:
            data (List[Any]): data to be logged in
                the format [pointcloud, steer, speed].
        """

        timestamp = datetime.timestamp(datetime.now())
        row = f"{timestamp}/{data[0]}/{data[1]}/{data[2]}\n"

        self.log_file.write(row)
        self.counter += 1

        if self.counter >= 10:
            self.log_file.close()
            self.log_file = open(self.filename, "+a", encoding="utf8")

            self.counter = 0

    def info(self, message: Any) -> None:
        """
        Displays information on the terminal with its timestamp.

        Args:
            message (Any): message to be displayed on the console.
        """

        timestamp = datetime.now().strftime("%H:%M:%S")

        print(f"{GREEN}{timestamp} {BLUE}[INFO]{NORMAL} {message}")

    def close(self) -> None:
        """
        Properly closes log file.
        """

        self.log_file.close()
