import multiprocessing as mp
import time
import logger as log
import numpy as np
import matplotlib.pyplot as plt
from core import RPLidar, RPLidarException
from constants import LIDAR_BAUDRATE, LIDAR_HEADING_OFFSET_DEG, LIDAR_FOV_FILTER

logger = None

def lidar_process(queue, stop_event, logger_instance, port="/dev/ttyUSB", baudrate=LIDAR_BAUDRATE):
    """
    Child process that continuously reads from the LIDAR and sends data to the queue.
    """
    lidar = None
    logger = logger_instance
    try:
        # Setup LIDAR
        lidar = RPLidar(port, baudrate=baudrate)
        lidar.connect()
        lidar.start_motor()
        lidar.start()
        logger.info("[LidarProcess] LIDAR started.")

        pre_filtered_distances = np.zeros(360, dtype=float)

        # Non-blocking read with a short timeout
        scans = lidar.iter_scans()

        # "scans" is typically a list of scan “packets”
        # Each element is [(quality, angle, distance), ...]
        for scan in scans:
            #print("Running")
            if stop_event.is_set():
                logger.info("[LidarProcess] Detected Lidar Loop Stop Request")
                lidar.stop()
                lidar.stop_motor()
                lidar.disconnect()
                break

            # Convert to np.array: shape (N, 3) = (quality, angle, distance)
            scan_array = np.array(scan)
            angles = scan_array[:, 1]
            lidar_readings = scan_array[:, 2] / 1000.0  # mm to meters

            # Round angles to nearest int [0..359]
            indices = np.round(angles).astype(int)
            indices = np.clip(indices, 0, 359)
            pre_filtered_distances[indices] = lidar_readings

            # Shift for heading offset
            shifted_distances = np.roll(pre_filtered_distances,
                                        LIDAR_HEADING_OFFSET_DEG)

            # Apply Field of View filter
            half_fov = LIDAR_FOV_FILTER / 2.0
            angle_array = np.arange(360)
            diffs = (angle_array - 0) % 360
            keep_mask = ((diffs <= half_fov) |
                            (diffs >= 360 - half_fov))
            shifted_distances[~keep_mask] = 0.0

            #Log LIDAR data
            logger.logSensor(log.SENSOR.LIDAR, shifted_distances.tolist())

            # Send data to the queue if there's space
            if not queue.full():
                queue.put(shifted_distances.copy())

    except KeyboardInterrupt:
        logger_instance.info("[LidarProcess] KeyboardInterrupt detected. Stopping...")
        stop_event.set()
    except (RPLidarException, Exception) as e:
        logger.info(f"[LidarProcess] LIDAR error exception: {e}")
        stop_event.set()
    finally:
        if lidar is not None:
            logger.info("[LidarProcess] Stopping LIDAR...")
            try:
                stop_event.set()
                lidar.stop()
                lidar.stop_motor()
                lidar.disconnect()
            except Exception as e:
                logger.info(f"[LidarProcess] Error stopping LIDAR exception: {e}")
                stop_event.set()

        logger.info("[LidarProcess] Stopped.")
    
    logger.info("[LidarProcess] Completelly ended")
    

def plot_process(queue, stop_event):
    """
    Main process loop for plotting. Stops when LIDAR process stops.
    """
    plt.ion()
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})

    # Ensure 0° is at the top and angles go clockwise
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 5)

    try:
        while not stop_event.is_set():  # Stop if lidar_process stops
            if not queue.empty():
                distances = queue.get()
                ax.clear()

                # Maintain the same settings after clearing
                ax.set_theta_zero_location("N")
                ax.set_theta_direction(1)
                ax.set_ylim(0, 5)

                # Convert angles to radians
                angles = np.radians(np.arange(360, 0, -1))
                ax.scatter(angles, distances, c="red", s=5)

                plt.pause(0.05)  # short pause to refresh plot

            time.sleep(0.01)  # avoid busy-loop

    except KeyboardInterrupt:
        #print("[PlotProcess] Plotting stopped by user.")
        logger.info("[PlotProcess] Plotting stopped by user.")
    finally:
        plt.ioff()
        plt.close()
        logger.info("[PlotProcess] Stopped.")

if __name__ == "__main__":
    # Create a multiprocessing queue to exchange data between processes
    logger = log.Logger()
    data_queue = mp.Queue(maxsize=1)

    # Create a stop event to signal process termination
    stop_event = mp.Event()
    
    # Start LIDAR process
    lidar_proc = mp.Process(target=lidar_process, args=(data_queue, stop_event, logger))
    lidar_proc.start()

    # Start plot process
    try:
        plot_process(data_queue, stop_event)
    finally:
        logger.info("[Main] Terminating LIDAR process...")
        stop_event.set()
        lidar_proc.join()
        logger.info("[Main] Processes terminated.")
