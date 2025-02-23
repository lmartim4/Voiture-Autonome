import csv
from collections import defaultdict

def load_sensor_data(file_path: str) -> dict:
    """
    Loads sensor data from a CSV file and organizes it into a dictionary.

    Args:
        file_path (str): The path to the CSV file.

    Returns:
        dict: A dictionary where the keys are sensor names and the values are dictionaries
              mapping timestamps to sensor readings.
              Example: data["LIDAR"][1676543210.123] = [1.0, 2.0, 3.0]
    """
    data = defaultdict(lambda: defaultdict(list))

    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter='/')
        for row in reader:
            if len(row) >= 3:
                timestamp = float(row[0])
                sensor_name = row[1]
                reading_str = row[2]

                # Attempt to convert the reading to a list of floats
                try:
                    # Remove brackets and split by comma
                    reading = [float(x) for x in reading_str.strip('[]').split(',')]
                except ValueError:
                    # If it's not a list of floats, store the string as is
                    reading = reading_str.strip()

                data[sensor_name][timestamp] = reading
            else:
                print(f"Skipping malformed row: {row}")

    return dict(data)

# Example usage:
file_path = '/home/ensta/Voiture-Autonome/logs/2025-02-23/17-40-38_sensors.csv'
sensor_data = load_sensor_data(file_path)

# Accessing data:
if "LIDAR" in sensor_data:
    timestamps = list(sensor_data["LIDAR"].keys())
    if timestamps:
        first_timestamp = timestamps[0]
        print(f"LIDAR data at timestamp {first_timestamp}: {sensor_data['LIDAR'][first_timestamp]}")
    else:
        print("No LIDAR data found.")
else:
    print("No LIDAR sensor found in the data.")