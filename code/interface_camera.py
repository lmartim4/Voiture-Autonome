from algorithm.interfaces import CameraInterface
from algorithm.control_camera import *
import numpy as np
import cv2
import time
import algorithm.voiture_logger as voiture_logger
from picamera2 import Picamera2

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

matplotlib.use('TkAgg')

class RealCameraInterface(CameraInterface):
    
    #THE IMPLEMENTATION OF THE ABSTRACT METHOD
    def get_camera_frame(self) -> np.ndarray:
        """Implementation of the abstract method to get a camera frame"""
        try:
            frame = self.picam2.capture_array()
            if frame is None:
                self.logger.logConsole("Camera frame could not be captured")
                return None
            
            # Rotate the frame 180 degrees
            frame = cv2.rotate(frame, cv2.ROTATE_180)
            return frame
        except Exception as e:
            self.logger.logConsole(f"Error capturing camera frame: {e}")
            return None
    
    def get_resolution(self) -> tuple[int, int]:
        """Returns the camera resolution as (width, height)."""
        return self.width, self.height
    
    #SORROUNDING CODE NEEDE FOR THE INTERFACE
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
        
    def cleanup(self):
        try:
            self.picam2.close()
            self.logger.logConsole("Camera resources cleaned up")
        except Exception as e:
            self.logger.logConsole(f"Error cleaning up camera resources: {e}")
          
    def debug_camera(self):
        """Opens a debug window with camera visualization and processing information"""
        self.logger.logConsole("Starting camera debug visualization")
        
        # Set up the figure for visualization
        fig = plt.figure(figsize=(12, 8))
        fig.canvas.manager.set_window_title('Camera Debug Visualization')
        
        # Create GridSpec to properly organize subplots
        gs = fig.add_gridspec(2, 3)
        
        # Set up subplots for different visualizations
        ax_original = fig.add_subplot(gs[0, 0])
        ax_red_mask = fig.add_subplot(gs[0, 1])
        ax_green_mask = fig.add_subplot(gs[0, 2])
        ax_visualization = fig.add_subplot(gs[1, 0:2])
        ax_buttons = fig.add_subplot(gs[1, 2])
        
        # Initialize image displays
        img_original = ax_original.imshow(np.zeros((self.height, self.width, 3), dtype=np.uint8))
        img_red_mask = ax_red_mask.imshow(np.zeros((self.height, self.width), dtype=np.uint8), cmap='gray')
        img_green_mask = ax_green_mask.imshow(np.zeros((self.height, self.width), dtype=np.uint8), cmap='gray')
        img_visualization = ax_visualization.imshow(np.zeros((self.height, self.width, 3), dtype=np.uint8))
        
        # Set titles
        ax_original.set_title('Original Frame')
        ax_red_mask.set_title('Red Mask')
        ax_green_mask.set_title('Green Mask')
        ax_visualization.set_title('Visualization with Overlay')
        
        # Remove axes ticks
        for ax in [ax_original, ax_red_mask, ax_green_mask, ax_visualization]:
            ax.set_xticks([])
            ax.set_yticks([])
                
        # Configure the buttons area
        ax_buttons.set_facecolor('lightgray')
        ax_buttons.set_title('Controls')
        ax_buttons.set_xticks([])
        ax_buttons.set_yticks([])
        
        # Create buttons directly in the subplot
        # Create a Mode toggle button
        mode_button_pos = [0.25, 0.6, 0.5, 0.2]  # Relative to the ax_buttons
        mode_button = plt.axes([
            ax_buttons.get_position().x0 + mode_button_pos[0] * ax_buttons.get_position().width,
            ax_buttons.get_position().y0 + mode_button_pos[1] * ax_buttons.get_position().height,
            mode_button_pos[2] * ax_buttons.get_position().width,
            mode_button_pos[3] * ax_buttons.get_position().height
        ])
        
        # Create a Capture button
        capture_button_pos = [0.25, 0.2, 0.5, 0.2]  # Relative to the ax_buttons
        capture_button = plt.axes([
            ax_buttons.get_position().x0 + capture_button_pos[0] * ax_buttons.get_position().width,
            ax_buttons.get_position().y0 + capture_button_pos[1] * ax_buttons.get_position().height,
            capture_button_pos[2] * ax_buttons.get_position().width,
            capture_button_pos[3] * ax_buttons.get_position().height
        ])
        
        # Create buttons
        button_toggle = Button(mode_button, 'Mode: Auto')
        button_capture = Button(capture_button, 'Capture Frame')
        
        # Style the buttons
        button_toggle.label.set_fontsize(10)
        button_capture.label.set_fontsize(10)
        
        # Flags to control the update loop and modes
        self.is_running = True  # Kept for compatibility with existing code
        self.auto_mode = True
        self.capture_frame = False
        
        def toggle_mode(event):
            self.auto_mode = not self.auto_mode
            button_toggle.label.set_text(f"Mode: {'Auto' if self.auto_mode else 'Manual'}")
            self.logger.logConsole(f"Switched to {'Auto' if self.auto_mode else 'Manual'} mode")
            fig.canvas.draw_idle()
        
        def capture_single_frame(event):
            if not self.auto_mode:
                self.capture_frame = True
                self.logger.logConsole("Manual frame capture triggered")
        
        # Connect button events
        button_toggle.on_clicked(toggle_mode)
        button_capture.on_clicked(capture_single_frame)
        
        # Set a key handler to close the window on ESC
        def on_key(event):
            if event.key == 'escape':
                self.logger.logConsole("Stopping debug visualization (ESC key)")
                self.is_running = False
                plt.close(fig)
        
        fig.canvas.mpl_connect('key_press_event', on_key)
        
        def update():
            last_frame = None
            last_processing_results = None
            
            while self.is_running:
                try:
                    process_new_frame = False
                    
                    # Determine if we should process a new frame
                    if self.auto_mode:
                        # In auto mode, continuously get new frames
                        frame = self.get_camera_frame()
                        if frame is not None:
                            process_new_frame = True
                    elif self.capture_frame:
                        # In manual mode, only process when capture button is clicked
                        frame = self.get_camera_frame()
                        if frame is not None:
                            process_new_frame = True
                            self.capture_frame = False  # Reset the capture flag
                            self.logger.logConsole("Manual frame captured and processed")
                    else:
                        # In manual mode, but no capture requested - use last frame if available
                        frame = last_frame
                    
                    if frame is None:
                        self.logger.logConsole("No frame available")
                        # Brief pause to reduce CPU usage
                        plt.pause(0.1)
                        continue
                                        
                    # Keep track of the last valid frame
                    last_frame = frame
                    
                    # Get frame dimensions
                    width, height = self.get_resolution()
                    
                    # Process the frame if needed
                    if process_new_frame:
                        # Note: extract_info expects RGB input, no need to convert again
                        avg_r, avg_g, count_r, count_g, detection_status, processing_results = extract_info(frame, width, height)
                        last_processing_results = processing_results
                    else:
                        # Use the last processing results if in manual mode and no new capture
                        processing_results = last_processing_results
                    
                    if processing_results:
                        # Update images in the figure
                        img_original.set_data(frame)
                        img_red_mask.set_data(processing_results['mask_r'])
                        img_green_mask.set_data(processing_results['mask_g'])
                        
                        # Create visualization with overlay
                        visualization = create_overlay_visualization(
                            frame, 
                            processing_results['mask_r'], 
                            processing_results['mask_g'], 
                            processing_results['avg_r'], 
                            processing_results['avg_g'], 
                            processing_results['status']
                        )
                        
                        if visualization is not None:
                            img_visualization.set_data(visualization)
                        
                    # Update the figure
                    fig.canvas.draw_idle()
                    fig.canvas.flush_events()
                    
                    # Brief pause to reduce CPU usage
                    plt.pause(0.1)
                    
                except Exception as e:
                    self.logger.logConsole(f"Error in debug visualization: {e}")
                    import traceback
                    traceback.print_exc()
                    break
    
        # Start update in the main thread (for matplotlib compatibility)
        update()
    
if __name__ == "__main__":
    try:
        print("Starting camera debug interface...")
        print("Press ESC key to exit")
        camera = RealCameraInterface()
        camera.debug_camera()
    except Exception as e:
        print(f"Error starting camera debug: {e}")
    finally:
        # Ensure cleanup is called when exiting
        try:
            camera.cleanup()
            print("Camera resources cleaned up")
        except:
            pass