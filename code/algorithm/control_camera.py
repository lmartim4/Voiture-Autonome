import cv2
from enum import Enum
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import os

class Color(Enum):
    RED = "RED"
    GREEN = "GREEN"
    NONE = "Undefined"

class DetectionStatus(Enum):
    RED_LEFT_GREEN_RIGHT = "RED TO THE LEFT AND GREEN TO THE RIGHT"
    GREEN_LEFT_RED_RIGHT = "GREEN TO THE LEFT AND RED TO THE RIGHT - ERRO"
    ONLY_RED = "ONLY SEE RED"
    ONLY_GREEN = "ONLY SEE GREEN"
    NONE = "NO COLOR DETECTED"

def convert_to_hsv(frame):
    if frame is None:
        return None
    
    try:
        return cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    except Exception as e:
        print(f"Error converting to HSV: {e}")
        return None

red_brighter_lower, red_brighter_upper = np.array([0, 100, 100]), np.array([10, 255, 255])
red_darker_lower, red_darker_upper = np.array([160, 100, 100]), np.array([180, 255, 255])
green_lower, green_upper = np.array([30, 50, 50]), np.array([80, 255, 255])

def create_color_masks(frame_hsv):
    """
    Create masks for red and green colors
    
    Args:
        frame_hsv: HSV frame
        
    Returns:
        tuple: (red_mask, green_mask) or (None, None) if frame is invalid
    """
    if frame_hsv is None:
        return None, None
    
    try:

        mask_r1 = cv2.inRange(frame_hsv, red_brighter_lower, red_brighter_upper)
        mask_r2 = cv2.inRange(frame_hsv, red_darker_lower, red_darker_upper)
        mask_r = cv2.bitwise_or(mask_r1, mask_r2)

        mask_g = cv2.inRange(frame_hsv, green_lower, green_upper)
        
        return mask_r, mask_g
    except Exception as e:
        print(f"Error creating color masks: {e}")
        return None, None

def calculate_color_positions(mask_r, mask_g):
    if mask_r is None or mask_g is None:
        return -1, -1
    
    try:
        # Calculate average position of red pixels
        stack_r = np.column_stack(np.where(mask_r > 0))
        avg_r = np.mean(stack_r[:, 1]) if stack_r.size > 0 else -1

        # Calculate average position of green pixels
        stack_g = np.column_stack(np.where(mask_g > 0))
        avg_g = np.mean(stack_g[:, 1]) if stack_g.size > 0 else -1
        
        return avg_r, avg_g
    except Exception as e:
        print(f"Error calculating color positions: {e}")
        return -1, -1

def calculate_color_ratios(mask_r, mask_g, width, height):
    if mask_r is None or mask_g is None:
        return 0, 0
    
    try:
        ratio_r = 100*np.count_nonzero(mask_r) / (width * height)
        ratio_g = 100*np.count_nonzero(mask_g) / (width * height)
        print(f"Dados: {ratio_r:.1f}%, {ratio_g:.1f}%")
        return ratio_r, ratio_g
    except Exception as e:
        print(f"Error calculating color ratios: {e}")
        return 0, 0

def determine_detection_status(avg_r, avg_g, ratio_r, ratio_g, min_ratio=3):
    red_detected = avg_r != -1 and ratio_r >= min_ratio
    green_detected = avg_g != -1 and ratio_g >= min_ratio
    
    if red_detected and green_detected:
        if avg_r < avg_g:
            return DetectionStatus.RED_LEFT_GREEN_RIGHT
        if avg_g < avg_r:
            return DetectionStatus.GREEN_LEFT_RED_RIGHT
        else:
            return DetectionStatus.NONE
    elif red_detected:
        return DetectionStatus.ONLY_RED
    elif green_detected:
        return DetectionStatus.ONLY_GREEN
    else:
        return DetectionStatus.NONE

def create_overlay_visualization(frame, mask_r, mask_g, avg_r, avg_g, status):
    if frame is None or mask_r is None or mask_g is None:
        return None
    
    try:
        # Create a copy of the frame for visualization
        vis_frame = frame.copy()
        
        # Ensure masks have the same dimensions as the frame
        if len(mask_r.shape) == 2:  # Single channel mask
            mask_r_3d = np.zeros(vis_frame.shape, dtype=np.uint8)
            mask_r_3d[:,:,0] = mask_r
            mask_r_3d[:,:,1] = mask_r
            mask_r_3d[:,:,2] = mask_r
        else:  # Already 3-channel
            mask_r_3d = mask_r
            
        if len(mask_g.shape) == 2:  # Single channel mask
            mask_g_3d = np.zeros(vis_frame.shape, dtype=np.uint8)
            mask_g_3d[:,:,0] = mask_g
            mask_g_3d[:,:,1] = mask_g
            mask_g_3d[:,:,2] = mask_g
        else:  # Already 3-channel
            mask_g_3d = mask_g
        
        # Overlay detected areas with semi-transparent colors
        red_overlay = np.zeros_like(vis_frame)
        green_overlay = np.zeros_like(vis_frame)
        
        # Red overlay - apply to all pixels where mask is non-zero
        red_overlay[:,:,2][mask_r_3d[:,:,0] > 0] = 255  # Red channel
        
        # Green overlay - apply to all pixels where mask is non-zero
        green_overlay[:,:,1][mask_g_3d[:,:,0] > 0] = 255  # Green channel
        
        # Apply overlays
        vis_frame = cv2.addWeighted(vis_frame, 1, red_overlay, 0.3, 0)
        vis_frame = cv2.addWeighted(vis_frame, 1, green_overlay, 0.3, 0)
        
        # Draw vertical lines showing average positions
        height = vis_frame.shape[0]
        if avg_r != -1:
            cv2.line(vis_frame, (int(avg_r), 0), (int(avg_r), height), (0, 0, 255), 2)  # BGR format
        if avg_g != -1:
            cv2.line(vis_frame, (int(avg_g), 0), (int(avg_g), height), (0, 255, 0), 2)
        
        # Add status text
        status_text = status.value
        cv2.putText(vis_frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (255, 255, 255), 2, cv2.LINE_AA)
        
        return vis_frame
    except Exception as e:
        print(f"Error creating visualization: {e}")
        return frame

def extract_info(frame, width, height):
    """
    Process frame and extract color information
    
    Args:
        frame: RGB frame
        width: Frame width
        height: Frame height
        
    Returns:
        tuple: (avg_r, avg_g, ratio_r, ratio_g, detection_status, processing_results)
    """
    if frame is None:
        return -1, -1, 0, 0, DetectionStatus.NONE
    
    try:
        # Convert frame to HSV
        frame_hsv = convert_to_hsv(frame)
        if frame_hsv is None:
            return -1, -1, 0, 0, DetectionStatus.NONE
        
        # Create color masks
        mask_r, mask_g = create_color_masks(frame_hsv)
        if mask_r is None or mask_g is None:
            return -1, -1, 0, 0, DetectionStatus.NONE
        
        # Calculate color positions
        avg_r, avg_g = calculate_color_positions(mask_r, mask_g)
        
        # Calculate color ratios
        ratio_r, ratio_g = calculate_color_ratios(mask_r, mask_g, width, height)
        
        # Determine detection status
        detection_status = determine_detection_status(avg_r, avg_g, ratio_r, ratio_g)
        
        # Compile processing results for visualization
        processing_results = {
            'frame_hsv': frame_hsv,
            'mask_r': mask_r,
            'mask_g': mask_g,
            'avg_r': avg_r,
            'avg_g': avg_g,
            'ratio_r': ratio_r,
            'ratio_g': ratio_g,
            'status': detection_status
        }
        
        return avg_r, avg_g, ratio_r, ratio_g, detection_status, processing_results
    
    except Exception as e:
        print(f"Error processing camera stream: {e}")
        return -1, -1, 0, 0, DetectionStatus.NONE