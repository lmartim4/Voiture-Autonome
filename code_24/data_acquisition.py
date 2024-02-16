import csv
import os
import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import time


def data_acquisition(filename1, filename2, filename3):
    """
    Prepares CSV files for storing data.

    This function takes three filenames as inputs, each corresponding to a specific type of data.
    
    Parameters:
    - filename1: A string, the filename for general data.
    - filename2: A string, the filename for lidar data.
    - filename3: A string, the filename for filtered lidar data.

    Returns:
    A list containing file objects corresponding to the opened files.
    """

    file_objs = []

    headers = [
        (filename1, ["TimeStamp", "Average Distance", "Motor Speed", "Raw Lidar Direction", "Car Direction"]),
        (filename2, ["Lidar Data"]),
        (filename3, ["Filtered Lidar Data"])
    ]

    for filename, header in headers:
        try:
            # Check and remove existing file path
            if os.path.exists(filename):
                os.remove(filename)

            # Open CSV file for writing
            file_obj = open(filename, 'a', newline='')

            # Check if file is empty (indicating no headers), then add headers
            if os.path.getsize(filename) == 0:
                csv_writer = csv.writer(file_obj, delimiter=',')
                csv_writer.writerow(header)

            file_objs.append(file_obj)

        except Exception as e:
            print(f"Error during data acquisition for {filename}: {e}")

    return file_objs


def data_writing(file_objs, GENERAL_LIST, LIDAR_LIST, FILTERED_LIDAR_LIST):
    """
    Writes car's information into specified CSV files.

    Parameters:
    - file_objs: A list containing three file objects.
    - GENERAL_LIST: A list containing general data.
    - LIDAR_LIST: A list containing lidar data.
    - FILTERED_LIDAR_LIST: A list containing filtered lidar data.

    Outputs:
    None
    """

    t, d_front, cyclerate_prop, angle_cible, cyclerate_dir = GENERAL_LIST
    file_obj1, file_obj2, file_obj3 = file_objs

    # Create CSV writers
    csv_writer1 = csv.writer(file_obj1, delimiter=',')
    csv_writer2 = csv.writer(file_obj2, delimiter=',')
    csv_writer3 = csv.writer(file_obj3, delimiter=',')

    # Write data into the CSV files
    csv_writer1.writerow([t, d_front, cyclerate_prop, angle_cible, cyclerate_dir])
    csv_writer2.writerow(LIDAR_LIST)
    csv_writer3.writerow(FILTERED_LIDAR_LIST)


def close_files(file_objs):
    """
    Closes all CSV files.

    Parameters:
    - file_objs: A list containing three file objects.

    Outputs:
    None
    """

    for file_obj in file_objs:
        file_obj.close()


def get_lidar_data(filename):
    """
    Reads Lidar data from a CSV file.

    Parameters:
    - filename: A string, the filename of the Lidar CSV file.

    Returns:
    A list of lists containing the Lidar data.
    """

    data = []

    with open(filename, 'r') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader, None)  # Skip header row
        for row in csv_reader:
            data.append([float(value) for value in row])

    return data


def plot_data(filename, title):
    """
    Plots data from a CSV file (general Data file).

    Parameters:
    - filename: A string, the filename of the General Data CSV file.
    - title: A string, the title for the plot.

    Outputs:
    None
    """

    timestamps = []
    average_distances = []
    motor_speeds = []
    raw_lidar_directions = []
    car_directions = []

    with open(filename, 'r') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)  # Skip header row

        for row in csv_reader:
            timestamps.append(float(row[0]))
            average_distances.append(float(row[1]))
            motor_speeds.append(float(row[2]))
            raw_lidar_directions.append(float(row[3]))
            car_directions.append(float(row[4]))

    plt.figure(figsize=(10, 6))

    plt.subplot(2, 2, 1)
    plt.plot(timestamps, average_distances, marker='o')
    plt.title('Average Distance')
    plt.xlabel('Time')
    plt.ylabel('Distance')

    plt.subplot(2, 2, 2)
    plt.plot(timestamps, motor_speeds, marker='o')
    plt.title('Motor Speed')
    plt.xlabel('Time')
    plt.ylabel('Speed')

    plt.subplot(2, 2, 3)
    plt.plot(timestamps, raw_lidar_directions, marker='o')
    plt.title('Raw Lidar Direction')
    plt.xlabel('Time')
    plt.ylabel('Direction')

    plt.subplot(2, 2, 4)
    plt.plot(timestamps, car_directions, marker='o')
    plt.title('Car Direction')
    plt.xlabel('Time')
    plt.ylabel('Direction')

    plt.suptitle(title)
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust layout for suptitle

    plt.savefig(filename.replace(".txt", ".png"), dpi=144)


def animate_lidar_data(lidar_filename, filtered_lidar_filename):
    """
    Animates Lidar and filtered Lidar data in a scatter plot.

    Parameters:
    - lidar_filename: A string, the filename of the Lidar CSV file.
    - filtered_lidar_filename: A string, the filename of the filtered Lidar CSV file.

    Outputs:
    None
    """

    fig, ax = plt.subplots()
    ax.set_title('Lidar and Filtered Lidar Data Animation')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')

    lidar_data = np.array(get_lidar_data(lidar_filename))
    filtered_lidar_data = np.array(get_lidar_data(filtered_lidar_filename))

    x_lidar = lidar_data[0, 2] * np.cos(np.radians(lidar_data[0, 1]))
    y_lidar = lidar_data[0, 2] * np.sin(np.radians(lidar_data[0, 1]))

    ax.scatter(x_lidar, y_lidar, color="red", label="Lidar Data")
    x_filtered_lidar = filtered_lidar_data[0, 2] * np.cos(np.radians(filtered_lidar_data[0, 1]))
    y_filtered_lidar = filtered_lidar_data[0, 2] * np.sin(np.radians(filtered_lidar_data[0, 1]))
    ax.scatter(x_filtered_lidar, y_filtered_lidar, color="green", label="Filtered Lidar Data")
    ax.legend()

    def update(frame):
        ax.set_title('Lidar and Filtered Lidar Data Animation')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')

        # Update Lidar Data
        x_lidar = lidar_data[frame, 2] * np.cos(np.radians(lidar_data[frame, 1]))
        y_lidar = lidar_data[frame, 2] * np.sin(np.radians(lidar_data[frame, 1]))
        ax.scatter(x_lidar, y_lidar,color="red")

        # Update Filtered Lidar Data
        x_filtered_lidar = filtered_lidar_data[frame, 2] * np.cos(np.radians(filtered_lidar_data[frame, 1]))
        y_filtered_lidar = filtered_lidar_data[frame, 2] * np.sin(np.radians(filtered_lidar_data[frame, 1]))
        ax.scatter(x_filtered_lidar, y_filtered_lidar,color="green")

    ani = animation.FuncAnimation(fig, update, frames=min(len(lidar_data),len(filtered_lidar_data)), repeat=False)

    writervideo = animation.FFMpegWriter(fps=60)
    ani.save(lidar_filename.replace(".txt", ".mp4"), writer=writervideo)
