from algorithm.interfaces import LiDarInterface
from algorithm_visualizer import *

import time
import numpy as np
import multiprocessing as mp
from rplidar import RPLidar, RPLidarException
import algorithm.voiture_logger as cl
from algorithm.constants import LIDAR_BAUDRATE, LIDAR_HEADING_OFFSET_DEG, LIDAR_FOV_FILTER, LIDAR_POINT_TIMEOUT_MS


class RPLidarReader(LiDarInterface):
    last_lidar_read = mp.Array('d', 360)
    last_lidar_update = mp.Value('d', 0.0)
    stop_event = mp.Event()

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = LIDAR_BAUDRATE,
        heading_offset_deg: int = LIDAR_HEADING_OFFSET_DEG,
        fov_filter: int = LIDAR_FOV_FILTER,
        point_timeout_ms: int = LIDAR_POINT_TIMEOUT_MS,
        sensor_name: str = "Lidar"
    ):
        
        # Store parameters
        self.port = port
        self.baudrate = baudrate
        self.heading_offset_deg = heading_offset_deg
        self.fov_filter = fov_filter
        self.point_timeout_ms = point_timeout_ms

        # Prepare multiprocessing shared state
        self.last_lidar_read = mp.Array('d', 360)  # shared array of doubles
        self.last_lidar_update = mp.Value('d', 0.0)  # shared double (timestamp)
        self.stop_event = mp.Event()
        self.restart_attempts = mp.Value('i', 0)  # Count restart attempts

        # Prepare logger
        self.sensor_logger_instance = cl.CentralLogger(sensor_name=sensor_name)
        self.sensor_logger = self.sensor_logger_instance.get_logger()

        # Start background process
        self._lidar_process = None
        self._start_lidar_process()

        self._plot_process = None

    def _start_lidar_process(self):
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
    
    
    def _run_lidar_process(self, port: str, baudrate: int):
        lidar = None
        sensor_logger_instance = self.sensor_logger_instance
        
        while(not self.stop_event.is_set()):
            try:
                # Initialize the LIDAR
                lidar = RPLidar(port, baudrate=baudrate)
                
                # Before connecting, make sure the serial port is clean
                # This accesses the underlying serial connection to flush any leftover data
                if hasattr(lidar, '_serial') and lidar._serial is not None:
                    lidar._serial.reset_input_buffer()
                    lidar._serial.reset_output_buffer()
                
                lidar.connect()
                
                # Additional buffer clearing after connection
                if hasattr(lidar, '_serial'):
                    lidar._serial.reset_input_buffer()
                    lidar._serial.reset_output_buffer()
                    
                lidar.start_motor()
                lidar.start()
                sensor_logger_instance.logConsole("[Lidar] LIDAR started.")

                pre_filtered_distances = np.zeros(360, dtype=float)
                last_update_times = np.zeros(360, dtype=float)
                
                # Initialize buffer error counter
                buffer_errors = 0
                max_buffer_errors = 3  # Maximum consecutive buffer errors before restart

                for scan in lidar.iter_scans():
                    if self.stop_event.is_set():
                        sensor_logger_instance.logConsole("[Lidar] Stop Request")
                        break

                    # Reset buffer error counter on successful scan
                    buffer_errors = 0
                    
                    # Process scan data (your existing code)
                    scan_array = np.array(scan)
                    angles = scan_array[:, 1]
                    distances_m = scan_array[:, 2] / 1000.0  # convert mm to meters

                    # Rest of your processing code...
                    indices = np.round(angles).astype(int)
                    indices = np.clip(indices, 0, 359)
                    
                    pre_filtered_distances[indices] = distances_m
                    last_update_times[indices] = time.time() * 1000
                    
                    shifted_distances = np.roll(pre_filtered_distances, self.heading_offset_deg)
                    
                    # Fill zeros by propagating last known reading
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
                
            except ValueError as e:
                error_str = str(e)
                if "too many values to unpack" in error_str:
                    buffer_errors += 1
                    sensor_logger_instance.logConsole(f"[Lidar] Buffer unpack error ({buffer_errors}/{max_buffer_errors}): {e}")
                    
                    # Try to clear the buffer without full restart if possible
                    if hasattr(lidar, '_serial') and buffer_errors < max_buffer_errors:
                        try:
                            sensor_logger_instance.logConsole("[Lidar] Attempting to clear buffer without restart...")
                            lidar._serial.reset_input_buffer()
                            time.sleep(0.2)  # Brief pause
                            continue
                        except Exception as clear_err:
                            sensor_logger_instance.logConsole(f"[Lidar] Failed to clear buffer: {clear_err}")
                            
                    # If we've had too many consecutive buffer errors or clearing failed, break to restart
                    break
                    
            except RPLidarException as e:
                error_str = str(e)
                if "descriptor" in error_str.lower() or "buffer" in error_str.lower():
                    buffer_errors += 1
                    sensor_logger_instance.logConsole(f"[Lidar] Buffer-related error ({buffer_errors}/{max_buffer_errors}): {e}")
                    
                    # Try to clear the buffer without full restart if possible
                    if hasattr(lidar, '_serial') and buffer_errors < max_buffer_errors:
                        try:
                            sensor_logger_instance.logConsole("[Lidar] Attempting to clear buffer without restart...")
                            lidar._serial.reset_input_buffer()
                            time.sleep(0.2)  # Brief pause
                            continue
                        except Exception as clear_err:
                            sensor_logger_instance.logConsole(f"[Lidar] Failed to clear buffer: {clear_err}")
                    
                    # If we've had too many consecutive buffer errors or clearing failed, break to restart
                    break
                else:
                    # For other RPLidar errors, log and restart
                    sensor_logger_instance.logConsole(f"[Lidar] LIDAR error exception: {e}")
                    break
                    
            except Exception as e:
                # For any other exception, log and restart
                sensor_logger_instance.logConsole(f"[Lidar] LIDAR error exception: {e}")
                break
                
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
                
                # Add a small delay before attempting restart
                if not self.stop_event.is_set():
                    time.sleep(1.0)  # Longer pause between full restarts
    
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
            self._lidar_process.join(timeout=2.0)
        
        if self._plot_process and self._plot_process.is_alive():
            self._plot_process.join(timeout=2.0)
            
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

if __name__ == "__main__":
    try:
        # Create a reader
        lidar_reader = RPLidarReader(
            port="/dev/ttyUSB0", 
            baudrate=LIDAR_BAUDRATE
        )
        
        nonzero_count = np.count_nonzero(lidar_reader.get_lidar_data())
        
        while(nonzero_count < 180/2):
            print("[Main] Waiting for lidar readings before start live plot.")
            nonzero_count = np.count_nonzero(lidar_reader.get_lidar_data())
            time.sleep(0.1)
        
        lidar_reader.start_live_plot()
        
        while not lidar_reader.stop_event.is_set():
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("[Main] Interrupted by user.")
    finally:
        # Clean up
        lidar_reader.stop()