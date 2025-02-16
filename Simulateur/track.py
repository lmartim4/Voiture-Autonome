import numpy as np
import cv2

from tile import Tile

import matplotlib
matplotlib.use("GTK3Agg")
import matplotlib.pyplot as plt

class Grid:
    """
    Represents the grid containing instances of Tile.
    """
    def __init__(self, tile_definitions, global_params):
        """
        Initializes the grid.

        tile_definitions: list - List of TileDefinition.
        global_params: dict - Global parameters for tiles.
        """
        self.rows = global_params["n_rows"]
        self.cols = global_params["n_cols"]
        self.tile_resolution = global_params["tile_resolution"]
        self.global_params = global_params
        self.grid = [[Tile(tile_definitions) for _ in range(self.cols)] for _ in range(self.rows)]

    def simulate_collapse(self):
        """
        Simulates the collapse process by filling the grid with specific tiles.
        """
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid[row][col].collapse()

    def plot_debug_grid(self):
        """
        Visualizes the current state of the grid with debug information.

        grid: Grid - Instance of the Grid class containing the current state of the track.
        """
        rows, cols = self.rows, self.cols
        fig, ax = plt.subplots(figsize=(cols * 1.5, rows * 1.5))  # Adjust figure size

        # Set grid limits
        ax.set_xlim(0, cols)
        ax.set_ylim(0, rows)
        ax.invert_yaxis()  # Align (0, 0) to the bottom-left corner

        # Draw grid lines
        for x in range(cols + 1):
            ax.axvline(x, color='black', linewidth=0.5)
        for y in range(rows + 1):
            ax.axhline(y, color='black', linewidth=0.5)

        # Fill in information for each cell
        for row in range(rows):
            for col in range(cols):
                tile = self.grid[row][col]
                if tile is None or not tile.collapsed:
                    # Uncollapsed cell
                    text = "?"
                else:
                    # Collapsed tile
                    definition = tile.collapsed["tile_definition"].name
                    orientation = tile.collapsed["orientation"] * 90
                    text = f"{definition}\n{orientation}°"

                # Add text to the center of the cell
                ax.text(
                    col + 0.5, row + 0.5, text,
                    fontsize=8, ha='center', va='center',
                    bbox=dict(boxstyle="round", facecolor="white", edgecolor="black", alpha=0.7)
                )

        # Configure plot
        ax.set_xticks(range(cols))
        ax.set_yticks(range(rows))
        ax.set_xticklabels(range(cols))
        ax.set_yticklabels(range(rows))
        ax.set_aspect('equal')
        ax.grid(False)

        plt.tight_layout()  # Automatically adjust layout
        plt.title("Current Grid State")
        plt.show()

    def generate_bitmap(self):
        """
        Generates the complete bitmap of the track based on the current grid.

        Returns:
        np.ndarray - Bitmap representing the entire track.
        """
        tile_size = self.global_params["tile_size"]
        bitmap = np.zeros((self.rows * self.tile_resolution, self.cols * self.tile_resolution))

        # Scale to map the global grid to the bitmap
        scale = self.tile_resolution / tile_size

        for row in range(self.rows):
            for col in range(self.cols):
                tile_data = self.grid[row][col]
                if tile_data is None or not tile_data.collapsed:
                    continue

                tile = tile_data.collapsed["tile_definition"]
                orientation = tile_data.collapsed["orientation"]

                # Generate bitmap for the specific tile
                local_bitmap = tile.generate_bitmap(
                    global_params=self.global_params,
                    grid_size=int(tile_size * scale),
                    orientation=orientation
                )

                # Calculate offset in the global grid
                offset_x = int(col * tile_size * scale)
                offset_y = int((self.rows - 1 - row) * tile_size * scale)  # Invert row order

                # Insert local bitmap into the global bitmap
                for i in range(local_bitmap.shape[0]):
                    for j in range(local_bitmap.shape[1]):
                        if local_bitmap[i, j] > 0:
                            bitmap[offset_y + i, offset_x + j] = 1

        return bitmap
    
    def dilate_track(self, bitmap):
        """
        Applies dilation to the track bitmap to "thicken" the lines.

        bitmap: np.ndarray - Matrix representing the track (0 = background, 1 = track).
        kernel_size: int - Kernel size for dilation.
        iterations: int - Number of dilation iterations.

        Returns:
        np.ndarray - Dilated bitmap.
        """
        
        kernel_size = self.global_params["dilation_kernel_size"]
        iterations = self.global_params["dilation_iter"]

        # Convert bitmap to binary format (0 and 255)
        binary_image = (bitmap * 255).astype(np.uint8)

        # Create a kernel (structuring element) for dilation
        kernel = np.ones((kernel_size, kernel_size), np.uint8)

        # Apply dilation
        dilated_image = cv2.dilate(binary_image, kernel, iterations=iterations)

        return dilated_image

    def keep_largest_track(self,bitmap):
        """
        Keeps only the two largest connected components (track) in the given binary bitmap.

        Parameters:
        - bitmap: np.ndarray (Binary matrix where track pixels are 1 and background is 0)

        Returns:
        - np.ndarray (Filtered bitmap with only the largest track)
        """

        # Ensure it's binary (in case of grayscale values)
        binary_bitmap = (bitmap > 0).astype(np.uint8)

        # Find connected components
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_bitmap, connectivity=8)

        if num_labels <= 2:
            return bitmap   # No need to filter if there are already at most 2 components

        # Get sizes of each component (excluding the background at index 0)
        component_sizes = stats[1:, cv2.CC_STAT_AREA]  # Ignore background

        # Get indices of the two largest components
        largest_indices = np.argsort(component_sizes)[-2:] + 1  # Add 1 to ignore background label

        # Create a mask for only the two largest components
        filtered_bitmap = np.isin(labels, largest_indices).astype(np.uint8) * 255
 

        return filtered_bitmap # Return a binary image again

    def crop_to_content(self,bitmap):
        """
        Automatically crops the image to the smallest bounding box containing the track.

        Parameters:
        - bitmap: np.ndarray (Binary matrix where track pixels are 1 and background is 0)

        Returns:
        - np.ndarray (Cropped bitmap)
        """
        # Find non-zero pixels (track area)
        coords = cv2.findNonZero(bitmap)

        if coords is None:
            return bitmap  # No need to crop if no track is found

        # Get bounding box
        x, y, w, h = cv2.boundingRect(coords)

        # Crop the image to this bounding box
        cropped_bitmap = bitmap[y:y+h, x:x+w]

        return cropped_bitmap
    
    
    def plot_bitmap(self, block=True):
        """
        Displays the generated bitmap of the track.
        """
        bitmap = self.generate_bitmap()

        # Fix the holes, thicken the walls
        bitmap = self.dilate_track(bitmap)
        
        # Keep only the largest track 
        bitmap = self.keep_largest_track(bitmap)

        # Crop the image to fit the track tightly
        bitmap = self.crop_to_content(bitmap)

        plt.imshow(bitmap, cmap='Greys', origin='lower')
        plt.title("Track Bitmap")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.show(block=block)

