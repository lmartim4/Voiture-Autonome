import cv2
import numpy as np

def find_nearest_track_edges(img, x, y):
    """
    Finds the nearest track edges (black pixels) in vertical and horizontal directions.
    """
    h, w = img.shape
    
    # Search up
    up_dist = next((i for i in range(y, -1, -1) if img[i, x] == 0), 0)
    # Search down
    down_dist = next((i for i in range(y, h) if img[i, x] == 0), h - 1)
    # Search left
    left_dist = next((i for i in range(x, -1, -1) if img[y, i] == 0), 0)
    # Search right
    right_dist = next((i for i in range(x, w) if img[y, i] == 0), w - 1)
    
    # Compute distances
    vertical_dist = down_dist - up_dist
    horizontal_dist = right_dist - left_dist
    
    return up_dist, down_dist, left_dist, right_dist, vertical_dist, horizontal_dist


def draw_start_finish_line(img, x, y, thickness=5):
    """
    Draws a red start/finish line at the closest track edge.
    """
    up, down, left, right, v_dist, h_dist = find_nearest_track_edges(img, x, y)
    img_colored = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    if v_dist < h_dist:
        # Draw vertical line
        cv2.line(img_colored, (x, up), (x, down), (0, 0, 255), thickness)
    else:
        # Draw horizontal line
        cv2.line(img_colored, (left, y), (right, y), (0, 0, 255), thickness)
    
    return img_colored


def on_mouse_click(event, x, y, flags, param):
    """
    Mouse callback function to place the start/finish line.
    """
    global track_img, display_img
    if event == cv2.EVENT_LBUTTONDOWN:
        # Transformar coordenadas para a imagem original
        x_orig = int(x * scale_x)
        y_orig = int(y * scale_y)

        display_img_resized = draw_start_finish_line(track_img, x_orig, y_orig)
        display_img = cv2.resize(display_img_resized, display_size, interpolation=cv2.INTER_AREA)
        
        cv2.imshow('Select Start/Finish Line', display_img)


if __name__ == "__main__":
    track_path = "tracks/track2.png"  # Modify this to the correct track image
    track_img = cv2.imread(track_path, cv2.IMREAD_GRAYSCALE)

    if track_img is None:
        raise FileNotFoundError(f"Error: Could not load image from {track_path}")

    # Get original dimensions
    orig_h, orig_w = track_img.shape

    # Compute new dimensions while keeping the aspect ratio
    max_size = 800  # Max width/height
    scale_factor = min(max_size / orig_w, max_size / orig_h)  # Scale based on the largest dimension
    new_w, new_h = int(orig_w * scale_factor), int(orig_h * scale_factor)

    # Scaling factors for mapping clicks
    scale_x = orig_w / new_w
    scale_y = orig_h / new_h

    # Resize image while keeping aspect ratio
    display_size = (new_w, new_h)
    display_img = cv2.resize(cv2.cvtColor(track_img, cv2.COLOR_GRAY2BGR), display_size, interpolation=cv2.INTER_AREA)

    print(f"Original image size: {track_img.shape}")
    print(f"Displayed image size: {display_size}")

    cv2.imshow('Select Start/Finish Line', display_img)
    cv2.setMouseCallback('Select Start/Finish Line', on_mouse_click)

    while True:
        key = cv2.waitKey(1)
        if key == 27 or cv2.getWindowProperty('Select Start/Finish Line', cv2.WND_PROP_VISIBLE) < 1:
            break  # Close window on ESC or clicking the "X" button

    cv2.destroyAllWindows()
