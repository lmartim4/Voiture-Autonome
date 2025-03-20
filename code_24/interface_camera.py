from interfaces import CameraInterface
import numpy as np
import cv2
from picamera2 import Picamera2
import voiture_logger

class RealCameraInterface(CameraInterface):
    def __init__(self, width=640, height=480):
        self.logger = voiture_logger.CentralLogger(sensor_name="RealCamera").get_logger()
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (width, height)},
            lores={"size": (width, height)}
        )
        self.picam2.configure(config)

        try:
            self.picam2.start()
            self.logger.info("Camera initialization successful")
        except Exception as e:
            self.logger.error(f"Camera initialization error: {e}")
            raise

        self.width = width
        self.height = height

    def get_camera_frame(self) -> np.ndarray:
        """
        Captures and returns the current camera frame.
        
        Returns:
            np.ndarray: The camera frame as a numpy array, or None if capture failed
        """
        try:
            frame = self.picam2.capture_array()
            if frame is None:
                self.logger.warning("Camera frame could not be captured")
            return frame
        except Exception as e:
            self.logger.error(f"Error capturing camera frame: {e}")
            return None

    def process_stream(self):
        """
        Processes the camera frame to detect red and green objects.
        
        Returns:
            tuple: (avg_red_x, avg_green_x, red_ratio, green_ratio)
        """
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

            return avg_r, avg_g, count_r, count_g
        
        except Exception as e:
            self.logger.error(f"Error processing camera stream: {e}")
            return -1, -1, 0, 0
            
    def cleanup(self):
        """
        Properly closes the camera resources.
        Should be called when the program ends.
        """
        try:
            self.picam2.close()
            self.logger.info("Camera resources cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up camera resources: {e}")


if __name__ == "__main__":
    # Simple test for the RealCameraInterface
    import time
    
    camera = RealCameraInterface()
    
    try:
        print("Starting camera test...")
        
        # Test capturing frames
        for i in range(5):
            print(f"Capturing frame {i+1}/5")
            frame = camera.get_camera_frame()
            if frame is not None:
                print(f"Frame shape: {frame.shape}")
            else:
                print("Failed to capture frame")
            time.sleep(1)
        
        # Test processing stream
        for i in range(5):
            print(f"Processing stream {i+1}/5")
            avg_r, avg_g, count_r, count_g = camera.process_stream()
            print(f"Red avg position: {avg_r}, Green avg position: {avg_g}")
            print(f"Red pixel ratio: {count_r:.4f}, Green pixel ratio: {count_g:.4f}")
            time.sleep(1)
            
        print("Camera test completed successfully!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during test: {e}")
    finally:
        camera.cleanup()
        print("Camera resources cleaned up")