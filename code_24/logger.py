import os
import pyperclip
from typing import Any, List
from datetime import datetime
from enum import Enum

NORMAL = "\33[0m"
GREEN = "\33[32m"
BLUE  = "\33[34m"
GRAY  = "\33[90m"
UNDERLINE = "\33[4m"

class SENSOR(Enum):
    SPEED_SENSOR    = 0
    REAR_DISTANCE   = 1
    BATTERY_VOLTAGE = 2
    STEER_CMD       = 3
    SPEED_CMD       = 4
    LIDAR           = 5

# CSV Headers
HEADER = "timestamp/speed_sensor/rear_distance/battery_voltage/steer/speed/pointcloud\n"
SENSOR_HEADER = "timestamp/sensor/data\n"

class Logger:
    def __init__(self, path: str = "../logs") -> None:
        """
        Initializes the Console object.

        Creates three log files using the code execution timestamp as filename:
        1) The main aggregated log file
        2) The sensor-specific log file
        3) The info log file, for storing console info prints

        Args:
            path (str, optional): logs folder path. Defaults to "../logs".
        """

        # ----------------------------------------------
        # Create a timestamped base name for logs
        # ----------------------------------------------
        timestamp_str = datetime.now().strftime("%Y-%m-%d/%H-%M-%S")
        base_path = os.path.join(path, *timestamp_str.split("/"))
        
        self.filename = base_path + ".csv"         # Main aggregated data
        self.sensor_filename = base_path + "_sensors.csv"  # Sensor-based data
        self.info_filename = base_path + "_info.log"       # Console info messages

        # ----------------------------------------------
        # Make sure directories exist
        # ----------------------------------------------
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)

        # ----------------------------------------------
        # Open the main log file
        # ----------------------------------------------
        self.file = open(self.filename, "a", encoding="utf8")
        self.file.write(HEADER)

        # ----------------------------------------------
        # Open the sensor log file
        # ----------------------------------------------
        self.sensor_file = open(self.sensor_filename, "a", encoding="utf8")
        self.sensor_file.write(SENSOR_HEADER)

        # ----------------------------------------------
        # Open the info log file
        # ----------------------------------------------
        self.info_file = open(self.info_filename, "a", encoding="utf8")

        # Internal counters for flushing
        self.counter = 0           # For main log
        self.sensor_counter = 0    # For sensor log

        # Notify user
        self.info(f"Data stored in {UNDERLINE}{self.filename}{NORMAL}")
        self.info(f"Sensor data stored in {UNDERLINE}{self.sensor_filename}{NORMAL}")
        self.info(f"Info logs stored in {UNDERLINE}{self.info_filename}{NORMAL}")

        # Copy multiplot command to clipboard
        pyperclip.copy(f"python multiplot.py \"{self.filename}\"")
        self.info(f"Multiplot command copied to clipboard\n")

    def log(self, data: List[Any]) -> None:
        """
        Appends a row of data to the main log file (aggregated metrics).
        Saves/flushes the file every 10 new lines.

        Args:
            data (List[Any]): e.g. [speed_sensor, rear_distance, battery_voltage, steer, speed, pointcloud]
        """

        timestamp = datetime.timestamp(datetime.now())
        row = "{}/{}/{}/{}/{}/{}/{}\n".format(timestamp, *data)
        self.file.write(row)
        self.counter += 1

        if self.counter > 20:
            self.file.close()
            self.file = open(self.filename, "a", encoding="utf8")
            self.counter = 0

    def logSensor(self, sensor: SENSOR, data: Any) -> None:
        """
        Logs a single sensor reading to the sensor-specific log file.

        Args:
            sensor (SENSOR): Which sensor is being logged, e.g. SENSOR.LIDAR
            data (Any): Data to be logged for that sensor (float, str, etc.)
        """
        timestamp = datetime.timestamp(datetime.now())
        row = f"{timestamp}/{sensor.name}/{data}\n"
        self.sensor_file.write(row)
        self.sensor_counter += 1

        if self.sensor_counter > 20:
            self.sensor_file.close()
            self.sensor_file = open(self.sensor_filename, "a", encoding="utf8")
            self.sensor_counter = 0

    def info(self, message: Any) -> None:
        """
        Prints colored info text to the console and logs it to the info file.

        Args:
            message (Any): message to be displayed and logged.
        """
        # Format a timestamp for display
        timestamp_str = datetime.now().strftime("%H:%M:%S")

        # Print to terminal (with color)
        print(f"{GREEN}{timestamp_str} {BLUE}[INFO]{NORMAL} {message}")
        
        # Also write to the info log file (without color codes)
        self.info_file.write(f"{timestamp_str} [INFO] {message}\n")

        # You can flush here if you want immediate writes
        self.info_file.flush()

    def close(self) -> None:
        """
        Properly closes all log files.
        """
        self.file.close()
        self.sensor_file.close()
        self.info_file.close()
