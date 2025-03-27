import matplotlib.pyplot as plt
import numpy as np
import cv2
import matplotlib
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib.backends.backend_agg import FigureCanvasAgg
import multiprocessing as mp
import time

class CameraVisualizer:
    """
    Visualizes camera processing results in real-time, showing both
    the original frame and detected red/green points with their average positions.
    """
    
    def __init__(self):
        # Set matplotlib to use a non-interactive backend for multiprocessing
        matplotlib.use('Agg')
        
        # Shared memory for camera data
        self.frame_data = mp.Array('B', 640 * 480 * 3)  # RGB frame data
        self.frame_shape = mp.Array('i', 3)  # Height, width, channels
        self.red_points = mp.Array('i', 640 * 480 * 2)  # x,y coordinates of red points
        self.green_points = mp.Array('i', 640 * 480 * 2)  # x,y coordinates of green points
        self.red_count = mp.Value('i', 0)  # Number of red points
        self.green_count = mp.Value('i', 0)  # Number of green points
        self.avg_r = mp.Value('d', -1.0)  # Average red x position
        self.avg_g = mp.Value('d', -1.0)  # Average green x position
        self.stop_event = mp.Event()
        self.update_event = mp.Event()
        
        # Start visualization process
        self.process = None
        
    def start(self):
        """Start the visualization process"""
        if self.process is not None and self.process.is_alive():
            print("[CameraVisualizer] Process already running")
            return
            
        self.process = mp.Process(
            target=self._run_visualization,
            daemon=True
        )
        self.process.start()
        print("[CameraVisualizer] Visualization process started")
        
    def stop(self):
        """Stop the visualization process"""
        self.stop_event.set()
        if self.process is not None and self.process.is_alive():
            self.process.join(timeout=2)
            if self.process.is_alive():
                self.process.terminate()
        print("[CameraVisualizer] Visualization process stopped")
        
    def update_data(self, frame, red_mask, green_mask, avg_r, avg_g):
        """
        Update the camera data in shared memory
        
        :param frame: RGB camera frame
        :param red_mask: Binary mask of red pixels
        :param green_mask: Binary mask of green pixels
        :param avg_r: Average position of red pixels
        :param avg_g: Average position of green pixels
        """
        if frame is None:
            return
            
        # Update frame data
        height, width, channels = frame.shape
        with self.frame_shape.get_lock():
            self.frame_shape[0] = height
            self.frame_shape[1] = width
            self.frame_shape[2] = channels
            
        # Copy frame to shared memory
        frame_flat = frame.flatten()
        with self.frame_data.get_lock():
            for i in range(min(len(frame_flat), len(self.frame_data))):
                self.frame_data[i] = frame_flat[i]
                
        # Extract red and green point coordinates
        red_y, red_x = np.where(red_mask > 0)
        green_y, green_x = np.where(green_mask > 0)
        
        # Limit to capacity of shared array
        max_points = len(self.red_points) // 2
        red_count = min(len(red_y), max_points)
        green_count = min(len(green_y), max_points)
        
        # Update red points
        with self.red_count.get_lock():
            self.red_count.value = red_count
            with self.red_points.get_lock():
                for i in range(red_count):
                    self.red_points[i*2] = red_x[i]
                    self.red_points[i*2+1] = red_y[i]
                    
        # Update green points
        with self.green_count.get_lock():
            self.green_count.value = green_count
            with self.green_points.get_lock():
                for i in range(green_count):
                    self.green_points[i*2] = green_x[i]
                    self.green_points[i*2+1] = green_y[i]
                    
        # Update average positions
        with self.avg_r.get_lock():
            self.avg_r.value = avg_r
            
        with self.avg_g.get_lock():
            self.avg_g.value = avg_g
            
        # Signal that data has been updated
        self.update_event.set()
        
    def _run_visualization(self):
        """Visualization process that runs in a separate process"""
        try:
            # Create figure and axes
            plt.ion()  # Interactive mode
            fig, ax = plt.subplots(figsize=(10, 6))
            
            frame_display = ax.imshow(np.zeros((480, 640, 3), dtype=np.uint8))
            red_scatter = ax.scatter([], [], color='red', s=1, alpha=0.5, label='Red Points')
            green_scatter = ax.scatter([], [], color='green', s=1, alpha=0.5, label='Green Points')
            red_avg_line = ax.axvline(x=0, color='red', linestyle='--', linewidth=2, visible=False)
            green_avg_line = ax.axvline(x=0, color='green', linestyle='--', linewidth=2, visible=False)
            
            # Add legend
            ax.legend(loc='upper right')
            ax.set_title('Camera Analysis')
            
            plt.tight_layout()
            plt.show(block=False)
            
            while not self.stop_event.is_set():
                if self.update_event.wait(timeout=0.1):
                    self.update_event.clear()
                    
                    # Get frame data
                    with self.frame_shape.get_lock():
                        height = self.frame_shape[0]
                        width = self.frame_shape[1]
                        channels = self.frame_shape[2]
                        
                    # Reconstruct frame
                    frame = np.zeros((height * width * channels), dtype=np.uint8)
                    with self.frame_data.get_lock():
                        for i in range(min(len(frame), len(self.frame_data))):
                            frame[i] = self.frame_data[i]
                    
                    frame = frame.reshape((height, width, channels))
                    
                    # Get red points
                    red_x = []
                    red_y = []
                    with self.red_count.get_lock():
                        red_count = self.red_count.value
                        with self.red_points.get_lock():
                            for i in range(red_count):
                                red_x.append(self.red_points[i*2])
                                red_y.append(self.red_points[i*2+1])
                                
                    # Get green points
                    green_x = []
                    green_y = []
                    with self.green_count.get_lock():
                        green_count = self.green_count.value
                        with self.green_points.get_lock():
                            for i in range(green_count):
                                green_x.append(self.green_points[i*2])
                                green_y.append(self.green_points[i*2+1])
                                
                    # Get average positions
                    with self.avg_r.get_lock():
                        avg_r = self.avg_r.value
                        
                    with self.avg_g.get_lock():
                        avg_g = self.avg_g.value
                        
                    # Update visualization
                    frame_display.set_data(frame)
                    red_scatter.set_offsets(np.column_stack((red_x, red_y)))
                    green_scatter.set_offsets(np.column_stack((green_x, green_y)))
                    
                    # Update average position lines
                    if avg_r >= 0:
                        red_avg_line.set_xdata([avg_r, avg_r])
                        red_avg_line.set_visible(True)
                    else:
                        red_avg_line.set_visible(False)
                        
                    if avg_g >= 0:
                        green_avg_line.set_xdata([avg_g, avg_g])
                        green_avg_line.set_visible(True)
                    else:
                        green_avg_line.set_visible(False)
                        
                    # Redraw
                    fig.canvas.draw_idle()
                    plt.pause(0.01)
                    
            plt.close(fig)
            
        except Exception as e:
            print(f"[CameraVisualizer] Error in visualization process: {e}")
            
        finally:
            plt.close('all')