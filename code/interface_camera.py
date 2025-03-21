from algorithm.interfaces import CameraInterface
import numpy as np
import cv2
from picamera2 import Picamera2
import algorithm.voiture_logger as voiture_logger

class RealCameraInterface(CameraInterface):
    def __init__(self, width=640, height=480):
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

            return avg_r, avg_g, count_r, count_g
        
        except Exception as e:
            self.logger.logConsole(f"Error processing camera stream: {e}")
            return -1, -1, 0, 0
            
    def cleanup(self):
        try:
            self.picam2.close()
            self.logger.logConsole("Camera resources cleaned up")
        except Exception as e:
            self.logger.logConsole(f"Error cleaning up camera resources: {e}")


if __name__ == "__main__":
    import os
    import datetime
    import time
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Camera test script with image saving')
    parser.add_argument('--width', type=int, default=640, help='Camera frame width')
    parser.add_argument('--height', type=int, default=480, help='Camera frame height')
    parser.add_argument('--frames', type=int, default=5, help='Number of frames to capture')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between frames in seconds')
    parser.add_argument('--output', type=str, default='CameraTests', help='Output folder for saved images')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Images will be saved to: {output_dir}")
    
    # Initialize camera with specified dimensions
    camera = RealCameraInterface(width=args.width, height=args.height)
    
    # Create an image log file
    log_file = os.path.join(output_dir, "test_log.txt")
    with open(log_file, 'w') as f:
        f.write(f"Camera Test Log - {timestamp}\n")
        f.write(f"Resolution: {args.width}x{args.height}\n")
        f.write(f"Number of frames: {args.frames}\n")
        f.write(f"Delay between frames: {args.delay} seconds\n\n")
    
    try:
        print(f"Starting camera test with {args.width}x{args.height} resolution...")
        
        # Test capturing frames
        print("\n--- Frame Capture Test ---")
        for i in range(args.frames):
            print(f"Capturing frame {i+1}/{args.frames}")
            frame = camera.get_camera_frame()
            
            if frame is not None:
                print(f"Frame shape: {frame.shape}, Type: {frame.dtype}")
                
                # Save the raw frame
                frame_filename = os.path.join(output_dir, f"frame_{i+1:02d}.png")
                cv2.imwrite(frame_filename, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                
                # Log frame info
                with open(log_file, 'a') as f:
                    f.write(f"Frame {i+1}: Saved to {frame_filename}\n")
                    f.write(f"  Shape: {frame.shape}, Min: {frame.min()}, Max: {frame.max()}\n")
            else:
                print("Failed to capture frame")
                with open(log_file, 'a') as f:
                    f.write(f"Frame {i+1}: Failed to capture\n")
            
            time.sleep(args.delay)
        
        # Test processing stream
        print("\n--- Stream Processing Test ---")
        for i in range(args.frames):
            print(f"Processing stream {i+1}/{args.frames}")
            avg_r, avg_g, count_r, count_g, frame, mask_r, mask_g = camera.process_stream()
            
            print(f"Red avg position: {avg_r:.2f}, Green avg position: {avg_g:.2f}")
            print(f"Red pixel ratio: {count_r:.4f}, Green pixel ratio: {count_g:.4f}")
            
            # Log processing results
            with open(log_file, 'a') as f:
                f.write(f"\nProcessing {i+1}:\n")
                f.write(f"  Red avg position: {avg_r:.2f}, Green avg position: {avg_g:.2f}\n")
                f.write(f"  Red pixel ratio: {count_r:.4f}, Green pixel ratio: {count_g:.4f}\n")
            
            if frame is not None:
                # Create a combined visualization
                vis_height = frame.shape[0]
                vis_width = frame.shape[1] * 3  # Original + red mask + green mask
                vis = np.zeros((vis_height, vis_width, 3), dtype=np.uint8)
                
                # Convert RGB to BGR for OpenCV saving
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # Place images side by side
                vis[:, 0:frame.shape[1]] = frame_bgr
                vis[:, frame.shape[1]:frame.shape[1]*2] = mask_r
                vis[:, frame.shape[1]*2:] = mask_g
                
                # Add text labels
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(vis, "Original", (10, 30), font, 0.7, (255, 255, 255), 2)
                cv2.putText(vis, "Red Mask", (frame.shape[1] + 10, 30), font, 0.7, (255, 255, 255), 2)
                cv2.putText(vis, "Green Mask", (frame.shape[1]*2 + 10, 30), font, 0.7, (255, 255, 255), 2)
                
                # Save visualization
                vis_filename = os.path.join(output_dir, f"processed_{i+1:02d}.png")
                cv2.imwrite(vis_filename, vis)
                
                # Save individual masks
                cv2.imwrite(os.path.join(output_dir, f"red_mask_{i+1:02d}.png"), mask_r)
                cv2.imwrite(os.path.join(output_dir, f"green_mask_{i+1:02d}.png"), mask_g)
                
                with open(log_file, 'a') as f:
                    f.write(f"  Saved visualization to {vis_filename}\n")
            
            time.sleep(args.delay)
            
        print("\nCamera test completed successfully!")
        print(f"All test results and images saved to {output_dir}")
        with open(log_file, 'a') as f:
            f.write("\nTest completed successfully!\n")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        with open(log_file, 'a') as f:
            f.write("\nTest interrupted by user\n")
    except Exception as e:
        print(f"\nError during test: {e}")
        with open(log_file, 'a') as f:
            f.write(f"\nError during test: {e}\n")
    finally:
        camera.cleanup()
        print("Camera resources cleaned up")