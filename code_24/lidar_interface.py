import multiprocessing as mp
import time
import numpy as np
import matplotlib.pyplot as plt
from core import RPLidar, RPLidarException
from logger import Logger, SENSOR
from constants import LIDAR_BAUDRATE, LIDAR_HEADING_OFFSET_DEG, LIDAR_FOV_FILTER

console = Logger()

def lidar_process(queue, port="/dev/ttyUSB", baudrate=LIDAR_BAUDRATE):
    """
    Child process that continuously reads from the LIDAR and sends data to the queue.
    """
    lidar = None
    try:
        # Setup LIDAR
        lidar = RPLidar(port, baudrate=baudrate)
        lidar.connect()
        lidar.start_motor()
        lidar.start()
        console.info("[LidarProcess] LIDAR started.")

        pre_filtred_distances = np.zeros(360, dtype=float)
        for scan in lidar.iter_scans():
            # Convert to np array: each entry is (quality, angle, distance)
            scan_array = np.array(scan)

            angles = scan_array[:, 1]
            lidar_readings = scan_array[:, 2] / 1000.0  # mm to meters

            # Round angles to nearest int [0..359]
            indices = np.round(angles).astype(int)
            indices = np.clip(indices, 0, 359)
            pre_filtred_distances[indices] = lidar_readings

            # 1) Shift for heading offset so that 0° is "forward"
            shifted_distances = np.roll(pre_filtred_distances, LIDAR_HEADING_OFFSET_DEG)

            # 2) Keep only LIDAR_FOV_FILTER degrees around 0°
            #    i.e. if LIDAR_FOV_FILTER=180, we keep ±90° around 0.
            half_fov = LIDAR_FOV_FILTER / 2.0

            # Create angle array [0..359]
            angle_array = np.arange(360)

            # Compute how far each angle is from 0° in the "circular" sense
            # Then keep only those angles that are within ±(FOV/2)
            #  - (diffs <= half_fov) covers angles near 0
            #  - (diffs >= 360 - half_fov) covers angles near 359..360 that wrap around
            diffs = (angle_array - 0) % 360
            keep_mask = (diffs <= half_fov) | (diffs >= 360 - half_fov)

            # 3) Zero out anything outside this FOV
            shifted_distances[~keep_mask] = 0.0
            # If you prefer to mark them as invalid, you could do:
            # shifted_distances[~keep_mask] = np.nan


            console.logSensor(SENSOR.LIDAR, shifted_distances)
            
            # Put new distances into the queue
            if not queue.full():
                queue.put(shifted_distances.copy())

    except (RPLidarException, Exception) as e:
        console.info(f"[LidarProcess] LIDAR error: {e}")

    finally:
        if lidar:
            console.info("[LidarProcess] Stopping LIDAR...")
            try:
                lidar.stop()
                lidar.stop_motor()
                lidar.disconnect()
            except Exception as e:
                console.warning(f"[LidarProcess] Error stopping LIDAR: {e}")


def plot_process(queue):
    """
    Main process loop for plotting. Continuously reads from the queue and updates the plot.
    """
    plt.ion()
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})

    # Ensure 0° is at the top and angles go clockwise
    ax.set_theta_zero_location("N")  # 'N' sets 0° at the top
    ax.set_theta_direction(-1)  # Makes angles increase clockwise
    ax.set_ylim(0, 5)  # Adjust to your max range

    try:
        while True:
            if not queue.empty():
                distances = queue.get()
                ax.clear()

                # Maintain the same settings after clearing
                ax.set_theta_zero_location("N")
                ax.set_theta_direction(1)
                ax.set_ylim(0, 5)

                # Convert angles to radians, but reverse the order to match clockwise rotation
                angles = np.radians(np.arange(360, 0, -1))
                ax.scatter(angles, distances, c="red", s=5)

                plt.pause(0.05)  # short pause so the plot refreshes

            time.sleep(0.01)  # avoid busy-loop

    except KeyboardInterrupt:
        console.info("[PlotProcess] Plotting stopped by user.")
    finally:
        plt.ioff()
        plt.close()



if __name__ == "__main__":
    # Create a multiprocessing queue to exchange data between processes
    data_queue = mp.Queue(maxsize=1)

    # Child process for LIDAR scanning
    lidar_proc = mp.Process(target=lidar_process, args=(data_queue,))
    lidar_proc.start()

    # Main process does plotting
    try:
        print(data_queue)
        plot_process(data_queue)
    finally:
        lidar_proc.terminate()
        lidar_proc.join()
