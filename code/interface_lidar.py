from algorithm.interfaces import LiDarInterface
from algorithm_visualizer import *

import time
import numpy as np
import multiprocessing as mp
from rplidar import RPLidar, RPLidarException
import algorithm.voiture_logger as cl
from algorithm.constants import LIDAR_BAUDRATE, LIDAR_HEADING_OFFSET_DEG, LIDAR_FOV_FILTER, LIDAR_POINT_TIMEOUT_MS


class RPLidarReader(LiDarInterface):
    """
    Implementation of LiDarInterface that uses RPLidar in a separate process
    to continuously read data. Call get_lidar_data() to retrieve the most recent
    360 readings (angle in [0..359], distance in meters).
    
    Features auto-restart capability if the LiDAR fails.
    """

    last_lidar_read = mp.Array('d', 360)
    last_lidar_update = mp.Value('d', 0.0)
    stop_event = mp.Event()
    restart_event = mp.Event()  # New event to signal need for restart

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = LIDAR_BAUDRATE,
        heading_offset_deg: int = LIDAR_HEADING_OFFSET_DEG,
        fov_filter: int = LIDAR_FOV_FILTER,
        point_timeout_ms: int = LIDAR_POINT_TIMEOUT_MS,
        sensor_name: str = "Lidar",
        max_restart_attempts: int = 5,  # New parameter for restart limits
        restart_delay_seconds: int = 3  # Delay between restart attempts
    ):
        """
        :param port: Serial port where the LiDAR is connected.
        :param baudrate: Baud rate to use for RPLidar.
        :param heading_offset_deg: Offset to apply to angles (shifts the 360 array).
        :param fov_filter: Field-of-view filter (keep data only within +/- fov_filter/2).
        :param point_timeout_ms: How long (in ms) a point can remain valid without an update.
        :param sensor_name: Name for logging.
        :param max_restart_attempts: Maximum number of restart attempts before giving up.
        :param restart_delay_seconds: Time to wait between restart attempts.
        """
        
        # Store parameters
        self.port = port
        self.baudrate = baudrate
        self.heading_offset_deg = heading_offset_deg
        self.fov_filter = fov_filter
        self.point_timeout_ms = point_timeout_ms
        self.max_restart_attempts = max_restart_attempts
        self.restart_delay_seconds = restart_delay_seconds

        # Prepare multiprocessing shared state
        self.last_lidar_read = mp.Array('d', 360)  # shared array of doubles
        self.last_lidar_update = mp.Value('d', 0.0)  # shared double (timestamp)
        self.stop_event = mp.Event()
        self.restart_event = mp.Event()
        self.restart_attempts = mp.Value('i', 0)  # Count restart attempts

        # Prepare logger
        self.sensor_logger_instance = cl.CentralLogger(sensor_name=sensor_name)
        self.sensor_logger = self.sensor_logger_instance.get_logger()

        # Start background process
        self._lidar_process = None
        self._start_lidar_process()

        self._plot_process = None
        self._watchdog_process = None
        self._start_watchdog_process()

    def _start_lidar_process(self):
        """Start the LiDAR reading process"""
        if self._lidar_process is not None and self._lidar_process.is_alive():
            self.sensor_logger.info("[LidarReader] Process already running.")
            return
            
        self._lidar_process = mp.Process(
            target=self._run_lidar_process,
            args=(
                self.port,
                self.baudrate,
            ),
            daemon=True
        )
        self._lidar_process.start()
        self.sensor_logger.info("[LidarReader] Process started.")

    def _start_watchdog_process(self):
        """Start the watchdog process that monitors LiDAR and restarts if needed"""
        if self._watchdog_process is not None and self._watchdog_process.is_alive():
            return
            
        self._watchdog_process = mp.Process(
            target=self._run_watchdog_process,
            daemon=True
        )
        self._watchdog_process.start()
        self.sensor_logger.info("[LidarReader] Watchdog process started.")

    def _run_watchdog_process(self):
        """
        Watchdog process that monitors the LiDAR process and restarts it if needed.
        """
        try:
            while not self.stop_event.is_set():
                # Check if restart is needed
                if self.restart_event.is_set():
                    # Reset the restart event
                    self.restart_event.clear()
                    
                    # Check restart attempts
                    with self.restart_attempts.get_lock():
                        if self.restart_attempts.value >= self.max_restart_attempts:
                            self.sensor_logger.info(f"[LidarWatchdog] Max restart attempts ({self.max_restart_attempts}) reached. Giving up.")
                            self.stop_event.set()
                            break
                        
                        self.restart_attempts.value += 1
                        attempt = self.restart_attempts.value
                    
                    self.sensor_logger.info(f"[LidarWatchdog] Restart attempt {attempt}/{self.max_restart_attempts}")
                    
                    # Wait for process to terminate if it's still running
                    if self._lidar_process and self._lidar_process.is_alive():
                        self._lidar_process.join(timeout=5.0)
                        
                    # Wait before restart
                    self.sensor_logger.info(f"[LidarWatchdog] Waiting {self.restart_delay_seconds}s before restart...")
                    time.sleep(self.restart_delay_seconds)
                    
                    # Start a new process
                    self._start_lidar_process()
                    
                # Sleep to avoid CPU overuse
                time.sleep(1.0)
                
        except Exception as e:
            self.sensor_logger.info(f"[LidarWatchdog] Error: {e}")
        finally:
            self.sensor_logger.info("[LidarWatchdog] Watchdog process ended")

    def _run_lidar_process(
        self,
        port: str,
        baudrate: int
    ):
        """
        Child process that continuously reads from the RPLidar device and updates
        the shared memory array with 360 distance values.
        """
        lidar = None
        sensor_logger_instance = self.sensor_logger_instance  # For convenience

        try:
            lidar = RPLidar(port, baudrate=baudrate)
            lidar.connect()
            lidar.start_motor()
            lidar.start()
            sensor_logger_instance.logConsole("[Lidar] LIDAR started.")

            pre_filtered_distances = np.zeros(360, dtype=float)
            last_update_times = np.zeros(360, dtype=float)

            for scan in lidar.iter_scans():
                if self.stop_event.is_set():
                    sensor_logger_instance.logConsole("[Lidar] Stop Request")
                    break

                # Convert to np.array: shape (N, 3) = (quality, angle, distance)
                scan_array = np.array(scan)
                angles = scan_array[:, 1]
                distances_m = scan_array[:, 2] / 1000.0  # convert mm to meters

                # Round angles to nearest int in [0..359]
                indices = np.round(angles).astype(int)
                indices = np.clip(indices, 0, 359)

                # Update pre_filtered_distances and last_update_times
                pre_filtered_distances[indices] = distances_m
                last_update_times[indices] = time.time() * 1000  # store in ms

                # Shift for heading offset
                shifted_distances = np.roll(pre_filtered_distances, self.heading_offset_deg)

                # Fill zeros by propagating last known reading (optional smoothing trick)
                for i in range(1, 360):
                    if shifted_distances[i] == 0.0:
                        shifted_distances[i] = shifted_distances[i - 1]

                # Apply Field of View filter
                half_fov = self.fov_filter / 2.0
                angle_array = np.arange(360)
                diffs = (angle_array - 0) % 360
                keep_mask = ((diffs <= half_fov) | (diffs >= 360 - half_fov))
                shifted_distances[~keep_mask] = 0.0

                # Apply timeout
                current_time = time.time() * 1000  # ms
                time_diffs = current_time - last_update_times
                expired_mask = (time_diffs > self.point_timeout_ms) & (last_update_times > 0)
                shifted_distances[expired_mask] = 0.0
                last_update_times[expired_mask] = -1.0

                # Log data if desired
                self.sensor_logger.info(shifted_distances.tolist())

                # Copy to shared memory
                with self.last_lidar_read.get_lock():
                    for i in range(360):
                        self.last_lidar_read[i] = shifted_distances[i]
                    with self.last_lidar_update.get_lock():
                        self.last_lidar_update.value = time.time()

        except KeyboardInterrupt:
            sensor_logger_instance.logConsole("[Lidar] KeyboardInterrupt detected. Stopping...")
            self.stop_event.set()
        except (RPLidarException, Exception) as e:
            sensor_logger_instance.logConsole(f"[Lidar] LIDAR error exception: {e}")
            
            # Instead of stopping, trigger restart if not already stopping
            if not self.stop_event.is_set():
                sensor_logger_instance.logConsole("[Lidar] Triggering restart...")
                self.restart_event.set()
            
        finally:
            if lidar is not None:
                sensor_logger_instance.logConsole("[Lidar] Stopping LIDAR...")
                try:
                    lidar.stop()
                    lidar.stop_motor()
                    lidar.disconnect()
                except Exception as e:
                    sensor_logger_instance.logConsole(f"[Lidar] Error stopping LIDAR: {e}")

            sensor_logger_instance.logConsole("[Lidar] Stopped.")

    def _plot_process_function(
        self,
        last_lidar_read: mp.Array,
        last_lidar_update: mp.Value,
        stop_event: mp.Event
    ):
        """
        Runs in a separate process. Continuously fetches the LiDAR data from 
        shared memory and updates a live plot.
        """
        lidar_vis = VoitureAlgorithmPlotter()  # Replace with your plotting class

        last_handled_time = 0.0

        try:
            while not stop_event.is_set():
                # Check if there's fresh data
                with last_lidar_update.get_lock():
                    # If last_lidar_update is newer than last_handled_time => new data
                    if last_lidar_update.value > last_handled_time:
                        last_handled_time = last_lidar_update.value
                    else:
                        # No new data, slight pause
                        time.sleep(0.05)
                        continue

                # Copy the data out of shared memory
                lidar_data = np.zeros(360, dtype=float)
                with last_lidar_read.get_lock():
                    for i in range(360):
                        lidar_data[i] = last_lidar_read[i]

                # Update the visualization
                lidar_vis.updateView(lidar_data)

                # Give matplotlib time to draw
                plt.pause(0.01)
                time.sleep(0.05)

        except KeyboardInterrupt:
            self.sensor_logger.info("[PlotProcess] Stopped by user.")
        finally:
            # Close the figure
            plt.ioff()
            plt.close()

    def stop(self):
        """
        Stops the LIDAR reading process and cleans up.
        """
        self.sensor_logger_instance.logConsole("[LidarReader] Stopping...")
        self.stop_event.set()
        
        if self._lidar_process and self._lidar_process.is_alive():
            self._lidar_process.join(timeout=5.0)
            
        if self._watchdog_process and self._watchdog_process.is_alive():
            self._watchdog_process.join(timeout=5.0)
            
        if self._plot_process and self._plot_process.is_alive():
            self._plot_process.join(timeout=5.0)
            
        self.sensor_logger_instance.logConsole("[LidarReader] All processes stopped.")

    def get_lidar_data(self) -> np.ndarray:
        """
        Retrieves the latest LiDAR data from shared memory as a NumPy array of shape (360,).
        Angle i corresponds to distance in meters at angle i degrees.
        """
        data_copy = np.zeros(360, dtype=float)
        with self.last_lidar_read.get_lock():
            for i in range(360):
                data_copy[i] = self.last_lidar_read[i]
        return data_copy

    def start_live_plot(self):
        """
        Spawn a new process that reads the shared memory data and plots it in real time.
        """
        if self._plot_process is not None and self._plot_process.is_alive():
            self.sensor_logger.info("[LidarReader] Plot process already running.")
            return

        self._plot_process = mp.Process(
            target=self._plot_process_function,
            args=(self.last_lidar_read, self.last_lidar_update, self.stop_event),
            daemon=True
        )
        self._plot_process.start()
        self.sensor_logger.info("[LidarReader] Live plot process started.")
        
    def manual_restart(self):
        """
        Manually trigger a restart of the LiDAR process.
        """
        self.sensor_logger_instance.logConsole("[LidarReader] Manual restart requested")
        # Reset restart attempts counter for manual restart
        with self.restart_attempts.get_lock():
            self.restart_attempts.value = 0
        self.restart_event.set()

if __name__ == "__main__":
    try:
        # Create a reader
        lidar_reader = RPLidarReader(
            port="/dev/ttyUSB0", 
            baudrate=LIDAR_BAUDRATE,
            max_restart_attempts=5,
            restart_delay_seconds=3
        )
        lidar_reader.start_live_plot()
        
        while not lidar_reader.stop_event.is_set():
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("[Main] Interrupted by user.")
    finally:
        # Clean up
        lidar_reader.stop()