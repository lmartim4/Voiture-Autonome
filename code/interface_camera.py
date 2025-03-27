from algorithm.interfaces import CameraInterface
import numpy as np
import cv2
from picamera2 import Picamera2
import algorithm.voiture_logger as voiture_logger

class RealCameraInterface(CameraInterface):
    def __init__(self, width=640, height=480, enable_visualization=True):
        self.logger = voiture_logger.CentralLogger(sensor_name="RealCamera")
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (width, height)},
            lores={"size": (width, height)}
        )
        self.picam2.configure(config)

        try:
            self.picam2.start()
            self.logger.logConsole("Camera initialization successful")
        except Exception as e:
            self.logger.logConsole(f"Camera initialization error: {e}")
            raise

        self.width = width
        self.height = height
        
       # Initialize visualizer
        #self.visualizer = None
       # if enable_visualization:
         #   try:
          #      from interface_camera_visualizer import CameraVisualizer
           #     self.visualizer = CameraVisualizer()
            #    self.visualizer.start()
             #   self.logger.logConsole("Camera visualization started")
            #except Exception as e:
             #   self.logger.logConsole(f"Camera visualization initialization error: {e}") """

    def get_camera_frame(self) -> np.ndarray:
        try:
            frame = self.picam2.capture_array()
            if frame is None:
                self.logger.logConsole("Camera frame could not be captured")
            return frame
        except Exception as e:
            self.logger.logConsole(f"Error capturing camera frame: {e}")
            return None

    def process_stream(self):
        frame = self.get_camera_frame()
        if frame is None:
            return -1, -1, 0, 0

        try:
            frame_hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

            # Color ranges for detection
            red_lower, red_upper = np.array([0, 150, 150]), np.array([10, 255, 255])
            green_lower, green_upper = np.array([50, 100, 100]), np.array([70, 255, 255])

            # Create masks for red and green colors
            mask_r = cv2.inRange(frame_hsv, red_lower, red_upper)
            mask_g = cv2.inRange(frame_hsv, green_lower, green_upper)

            # Calculate average position of red pixels
            stack_r = np.column_stack(np.where(mask_r > 0))
            avg_r = np.mean(stack_r[:, 1]) if stack_r.size > 0 else -1

            # Calculate average position of green pixels
            stack_g = np.column_stack(np.where(mask_g > 0))
            avg_g = np.mean(stack_g[:, 1]) if stack_g.size > 0 else -1

            # Calculate ratio of red and green pixels to total frame size
            count_r = np.count_nonzero(mask_r) / (self.width * self.height)
            count_g = np.count_nonzero(mask_g) / (self.width * self.height)
            
            # Update visualization if enabled
            if self.visualizer is not None:
                try:
                    # Convert masks to RGB for visualization
                    mask_r_rgb = cv2.cvtColor(mask_r, cv2.COLOR_GRAY2RGB)
                    mask_g_rgb = cv2.cvtColor(mask_g, cv2.COLOR_GRAY2RGB)
                    
                    self.visualizer.update_data(
                        frame=frame,
                        red_mask=mask_r,
                        green_mask=mask_g,
                        avg_r=avg_r,
                        avg_g=avg_g
                    )
                except Exception as e:
                    self.logger.logConsole(f"Error updating camera visualization: {e}")

            return avg_r, avg_g, count_r, count_g
        
        except Exception as e:
            self.logger.logConsole(f"Error processing camera stream: {e}")
            return -1, -1, 0, 0
            
    def cleanup(self):
        try:
            # Stop visualization if it's running
            if self.visualizer is not None:
                try:
                    self.visualizer.stop()
                    self.logger.logConsole("Camera visualization stopped")
                except Exception as e:
                    self.logger.logConsole(f"Error stopping camera visualization: {e}")
            
            # Close the camera
            self.picam2.close()
            self.logger.logConsole("Camera resources cleaned up")
        except Exception as e:
            self.logger.logConsole(f"Error cleaning up camera resources: {e}")