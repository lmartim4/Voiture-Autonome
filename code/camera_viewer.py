import numpy as np
import cv2
import matplotlib.pyplot as plt
import os
import glob
from picamera2 import Picamera2

def visualize_last_frame(output_dir=None):
    """
    Find and visualize the last captured frame with detection overlays
    
    Args:
        output_dir: Directory where images are saved. If None, uses the most recent directory in CameraTests/
    """
    # Find the most recent output directory if not specified
    if output_dir is None:
        base_dir = "CameraTests"
        if not os.path.exists(base_dir):
            print(f"Error: Base directory {base_dir} does not exist")
            return
            
        dirs = glob.glob(os.path.join(base_dir, "*"))
        if not dirs:
            print(f"Error: No test directories found in {base_dir}")
            return
            
        output_dir = max(dirs, key=os.path.getctime)
        print(f"Using most recent directory: {output_dir}")
    
    # Find the last frame image
    frame_files = sorted(glob.glob(os.path.join(output_dir, "frame_*.png")))
    if not frame_files:
        print(f"Error: No frame images found in {output_dir}")
        return
        
    last_frame_file = frame_files[-1]
    print(f"Visualizing last frame: {last_frame_file}")
    
    # Load the image
    frame = cv2.imread(last_frame_file)
    if frame is None:
        print(f"Error: Could not load image {last_frame_file}")
        return
        
    # Convert BGR to RGB for proper display
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Convert to HSV for color detection
    frame_hsv = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2HSV)
    
    # Color ranges for detection
    red_lower, red_upper = np.array([0, 150, 150]), np.array([10, 255, 255])
    green_lower, green_upper = np.array([50, 100, 100]), np.array([70, 255, 255])
    
    # Create masks for red and green colors
    mask_r = cv2.inRange(frame_hsv, red_lower, red_upper)
    mask_g = cv2.inRange(frame_hsv, green_lower, green_upper)
    
    # Find coordinates of red and green pixels
    red_points = np.column_stack(np.where(mask_r > 0))
    green_points = np.column_stack(np.where(mask_g > 0))
    
    # Calculate average position of red pixels (Y coordinate)
    avg_r = np.mean(red_points[:, 0]) if red_points.size > 0 else -1
    
    # Calculate average position of green pixels (Y coordinate)
    avg_g = np.mean(green_points[:, 0]) if green_points.size > 0 else -1
    
    # Calculate ratio of red and green pixels to total frame size
    height, width = frame_rgb.shape[:2]
    count_r = np.count_nonzero(mask_r) / (width * height)
    count_g = np.count_nonzero(mask_g) / (width * height)
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Camera Frame Analysis', fontsize=16)
    
    # Original image
    axes[0, 0].imshow(frame_rgb)
    axes[0, 0].set_title('Original Image')
    axes[0, 0].axis('on')
    
    # Red mask
    axes[0, 1].imshow(mask_r, cmap='gray')
    axes[0, 1].set_title(f'Red Mask (Ratio: {count_r:.4f})')
    axes[0, 1].axis('on')
    
    # Green mask
    axes[1, 0].imshow(mask_g, cmap='gray')
    axes[1, 0].set_title(f'Green Mask (Ratio: {count_g:.4f})')
    axes[1, 0].axis('on')
    
    # Combined visualization
    axes[1, 1].imshow(frame_rgb)
    axes[1, 1].set_title('Detection Points')
    axes[1, 1].axis('on')
    
    # Add red and green points to the visualization
    if red_points.size > 0:
        # For matplotlib, we need to flip the coordinates as it expects (x, y) but OpenCV provides (y, x)
        axes[1, 1].scatter(red_points[:, 1], red_points[:, 0], c='red', s=1, alpha=0.5)
        axes[1, 1].axhline(y=avg_r, color='red', linestyle='--', 
                        label=f'Red Avg Y: {avg_r:.2f}')
        
    if green_points.size > 0:
        axes[1, 1].scatter(green_points[:, 1], green_points[:, 0], c='green', s=1, alpha=0.5)
        axes[1, 1].axhline(y=avg_g, color='green', linestyle='--', 
                         label=f'Green Avg Y: {avg_g:.2f}')
    
    axes[1, 1].legend()
    
    # Display stats
    stats_text = (
        f"Red pixels: {len(red_points)}\n"
        f"Red ratio: {count_r:.6f}\n"
        f"Red avg Y: {avg_r:.2f}\n\n"
        f"Green pixels: {len(green_points)}\n"
        f"Green ratio: {count_g:.6f}\n"
        f"Green avg Y: {avg_g:.2f}"
    )
    
    # Add text box with stats
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    axes[1, 1].text(0.05, 0.95, stats_text, transform=axes[1, 1].transAxes, 
                  fontsize=9, verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    
    # Save the visualization
    vis_file = os.path.join(output_dir, "visualization_matplotlib.png")
    plt.savefig(vis_file)
    print(f"Visualization saved to: {vis_file}")
    
    # Show the plot
    plt.show()

def capture_and_visualize(width=640, height=480):
    """
    Capture a new frame and visualize it immediately
    """
    try:
        # Initialize camera
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(
            main={"size": (width, height)},
            lores={"size": (width, height)}
        )
        picam2.configure(config)
        picam2.start()
        print("Camera initialized")
        
        # Capture a frame
        frame = picam2.capture_array()
        picam2.close()
        
        if frame is None:
            print("Error: Failed to capture frame")
            return
            
        print(f"Frame captured: {frame.shape}")
        
        # Convert to RGB (PiCamera returns RGB, so we don't need to convert)
        frame_rgb = frame
        
        # Convert to HSV for color detection
        frame_hsv = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2HSV)
        
        # Color ranges for detection
        red_lower, red_upper = np.array([0, 150, 150]), np.array([10, 255, 255])
        green_lower, green_upper = np.array([50, 100, 100]), np.array([70, 255, 255])
        
        # Create masks for red and green colors
        mask_r = cv2.inRange(frame_hsv, red_lower, red_upper)
        mask_g = cv2.inRange(frame_hsv, green_lower, green_upper)
        
        # Find coordinates of red and green pixels
        red_points = np.column_stack(np.where(mask_r > 0))
        green_points = np.column_stack(np.where(mask_g > 0))
        
        # Calculate average position of red pixels (Y coordinate)
        avg_r = np.mean(red_points[:, 0]) if red_points.size > 0 else -1
        
        # Calculate average position of green pixels (Y coordinate)
        avg_g = np.mean(green_points[:, 0]) if green_points.size > 0 else -1
        
        # Calculate ratio of red and green pixels to total frame size
        height, width = frame_rgb.shape[:2]
        count_r = np.count_nonzero(mask_r) / (width * height)
        count_g = np.count_nonzero(mask_g) / (width * height)
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Live Camera Frame Analysis', fontsize=16)
        
        # Original image
        axes[0, 0].imshow(frame_rgb)
        axes[0, 0].set_title('Original Image')
        axes[0, 0].axis('on')
        
        # Red mask
        axes[0, 1].imshow(mask_r, cmap='gray')
        axes[0, 1].set_title(f'Red Mask (Ratio: {count_r:.4f})')
        axes[0, 1].axis('on')
        
        # Green mask
        axes[1, 0].imshow(mask_g, cmap='gray')
        axes[1, 0].set_title(f'Green Mask (Ratio: {count_g:.4f})')
        axes[1, 0].axis('on')
        
        # Combined visualization
        axes[1, 1].imshow(frame_rgb)
        axes[1, 1].set_title('Detection Points')
        axes[1, 1].axis('on')
        
        # Add red and green points to the visualization
        if red_points.size > 0:
            # For matplotlib, we need to flip the coordinates as it expects (x, y) but OpenCV provides (y, x)
            axes[1, 1].scatter(red_points[:, 1], red_points[:, 0], c='red', s=1, alpha=0.5)
            axes[1, 1].axhline(y=avg_r, color='red', linestyle='--', 
                            label=f'Red Avg Y: {avg_r:.2f}')
            
        if green_points.size > 0:
            axes[1, 1].scatter(green_points[:, 1], green_points[:, 0], c='green', s=1, alpha=0.5)
            axes[1, 1].axhline(y=avg_g, color='green', linestyle='--', 
                             label=f'Green Avg Y: {avg_g:.2f}')
        
        axes[1, 1].legend()
        
        # Display stats
        stats_text = (
            f"Red pixels: {len(red_points)}\n"
            f"Red ratio: {count_r:.6f}\n"
            f"Red avg Y: {avg_r:.2f}\n\n"
            f"Green pixels: {len(green_points)}\n"
            f"Green ratio: {count_g:.6f}\n"
            f"Green avg Y: {avg_g:.2f}"
        )
        
        # Add text box with stats
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        axes[1, 1].text(0.05, 0.95, stats_text, transform=axes[1, 1].transAxes, 
                      fontsize=9, verticalalignment='top', bbox=props)
        
        plt.tight_layout()
        
        # Save the visualization
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("LiveCaptures", exist_ok=True)
        vis_file = os.path.join("LiveCaptures", f"visualization_{timestamp}.png")
        plt.savefig(vis_file)
        print(f"Visualization saved to: {vis_file}")
        
        # Show the plot
        plt.show()
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up camera resources
        try:
            picam2.close()
        except:
            pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Camera visualization tool')
    parser.add_argument('--mode', choices=['last', 'live'], default='last',
                      help='Visualization mode: last (last saved frame) or live (capture new frame)')
    parser.add_argument('--dir', type=str, default=None,
                      help='Directory containing saved frames (used with --mode=last)')
    parser.add_argument('--width', type=int, default=640,
                      help='Camera width for live capture')
    parser.add_argument('--height', type=int, default=480,
                      help='Camera height for live capture')
                      
    args = parser.parse_args()
    
    if args.mode == 'last':
        visualize_last_frame(args.dir)
    else:
        capture_and_visualize(args.width, args.height)