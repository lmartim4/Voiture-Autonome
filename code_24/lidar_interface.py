import multiprocessing as mp
import time
import numpy as np
import matplotlib.pyplot as plt
from core import RPLidar, RPLidarException
from constants import LIDAR_BAUDRATE, LIDAR_HEADING_OFFSET_DEG, LIDAR_FOV_FILTER, LIDAR_POINT_TIMEOUT_MS
from algorithm_visualizer import VoitureAlgorithmPlotter
import central_logger as cl

lidar_vis = None

sensor_logger_instance = cl.CentralLogger(sensor_name="Lidar")
sensor_logger = sensor_logger_instance.get_logger()

def lidar_process(queue, stop_event, port="/dev/ttyUSB", baudrate=LIDAR_BAUDRATE):
    """
    Child process that continuously reads from the LIDAR and sends data to the queue.
    """
    
    lidar = None
    
    try:
        lidar = RPLidar(port, baudrate=baudrate)
        lidar.connect()
        lidar.start_motor()
        lidar.start()
        sensor_logger_instance.logConsole("[Lidar] LIDAR started.")

        pre_filtered_distances = np.zeros(360, dtype=float)
        last_update_times = np.zeros(360, dtype=float)


        scans = lidar.iter_scans()
        
        for scan in scans:
            if stop_event.is_set():
                sensor_logger_instance.logConsole("[Lidar] Stop Request")
                break

            # Convert to np.array: shape (N, 3) = (quality, angle, distance)
            scan_array = np.array(scan)
            angles = scan_array[:, 1]
            lidar_readings = scan_array[:, 2] / 1000.0  # mm to meters

            # Round angles to nearest int [0..359]
            indices = np.round(angles).astype(int)
            indices = np.clip(indices, 0, 359)
            pre_filtered_distances[indices] = lidar_readings
            
            last_update_times[indices] = time.time()*1000  # Store the last update time in milliseconds

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
            
            # Apply timeout
            current_time = time.time() * 1000  # Current time in milliseconds
            
            time_diffs = current_time - last_update_times
            valid_time_diffs = np.logical_and(time_diffs > LIDAR_POINT_TIMEOUT_MS, last_update_times > 0)
            
            ##print(f"clearing {shifted_distances[valid_time_diffs].size} lidar points due to timeout")
            shifted_distances[valid_time_diffs] = 0.0
            last_update_times[valid_time_diffs] = -1.0
            
            #Log LIDAR data
            sensor_logger.info(shifted_distances.tolist())

            # Send data to the queue if there's space
            if not queue.full():
                queue.put(shifted_distances.copy())

    except KeyboardInterrupt:
        sensor_logger_instance.logConsole("[Lidar] KeyboardInterrupt detected. Stopping...")
        stop_event.set()
    except (RPLidarException, Exception) as e:
        sensor_logger_instance.logConsole(f"[Lidar] LIDAR error exception: {e}")
        stop_event.set()
    finally:
        if lidar is not None:
            sensor_logger_instance.logConsole("[Lidar] Stopping LIDAR...")
            try:
                stop_event.set()
                lidar.stop()
                lidar.stop_motor()
                lidar.disconnect()
            except Exception as e:
                sensor_logger_instance.logConsole(f"[Lidar] Error stopping LIDAR exception: {e}")

        sensor_logger_instance.logConsole("[Lidar] Stopped.")
    
    sensor_logger_instance.logConsole("[Lidar] Completelly ended")
    

def plot_process(queue, stop_event):
    """
    Main process loop for plotting. Stops when LIDAR process stops or when the plot window is closed.
    """
    
    lidar_vis = VoitureAlgorithmPlotter()
    
    plt.ion()

    try:
        while not stop_event.is_set():
            if not queue.empty():
                distances = queue.get()
                lidar_vis.updateView(distances)

                plt.pause(0.05)

            time.sleep(0.01)

    except KeyboardInterrupt:
        sensor_logger_instance.logConsole("[PlotProcess] Plotting stopped by user.")
    finally:
        plt.ioff()
        plt.close()
        sensor_logger_instance.logConsole("[PlotProcess] Stopped.")

if __name__ == "__main__":    
    data_queue = mp.Queue(maxsize=1)
    stop_event = mp.Event()
    
    lidar_proc = mp.Process(target=lidar_process, args=(data_queue, stop_event))
    lidar_proc.start()

    try:
        plot_process(data_queue, stop_event)
    except KeyboardInterrupt:
        sensor_logger_instance.logConsole("[Main] KeyboardInterrupt received. Stopping processes.")
        stop_event.set()
    finally:
        sensor_logger_instance.logConsole("[Main] Terminating LIDAR process...")
        stop_event.set()
        lidar_proc.join()
        sensor_logger_instance.logConsole("[Main] Processes terminated.")
