import pygame
import numpy as np
import params
import os
from car import Car

class Environment:
    def __init__(self, map_name, max_size=500, padding_percent=0.05):
        """
        Initializes the simulation environment without display components.

        :param map_name: str - Name of the map file inside 'tracks/' folder.
        :param max_size: int - Maximum size (either width or height).
        :param padding_percent: float - Percentage of max_size to be used as padding.
        """
        pygame.init()
        
        # Movement parameters (kept in the environment)
        self.speed = params.default_speed
        self.rotation_speed = np.deg2rad(params.default_rotation_speed)
        
        # Car position and angle (kept in the environment)
        self.car_position = [0, 0]  # Will be updated after loading metadata
        self.car_angle_rad = 0      # Will be updated after loading metadata
        
        # Environment point cloud (detected points in global coordinates)
        self.global_point_cloud = []
        
        # Load external map
        self.external_map = pygame.image.load(f'tracks/{map_name}')
        
        # Load starting position from metadata
        self.load_metadata(map_name)
        
        # Format the map
        self.format_map(map_name, max_size, padding_percent)
        
        # Initialize the car (sensors only, no position)
        self.car = None  # Will be initialized after creating the original map
        
        # Create a copy of the original map for collision detection
        self.original_map = self.map.copy()
        
        # Initialize the car (with dimensions)
        self.car = Car(env_map=self.original_map, width=10, height=20)
        
    def format_map(self, map_name, max_size, padding_percent):
        """
        Formats the map for use in the simulation.
        
        :param map_name: str - Map file name.
        :param max_size: int - Maximum size.
        :param padding_percent: float - Padding percentage.
        """
        # Original dimensions
        self.map_width, self.map_height = self.external_map.get_width(), self.external_map.get_height()

        # Calculate scale factor while keeping aspect ratio
        scale_factor = min(max_size / self.map_width, max_size / self.map_height)

        # Calculate new dimensions after scaling
        new_width, new_height = int(self.map_width * scale_factor), int(self.map_height * scale_factor)

        # Calculate padding based on max_size and the given percentage
        padding = int(max_size * padding_percent)

        # Calculate final window dimensions including padding
        final_width = new_width + 2 * padding
        final_height = new_height + 2 * padding
        
        # Store dimensions for later use
        self.view_width = final_width
        self.view_height = final_height
        
        # Adjust starting position with scale and padding
        self.car_position = [int(self.start_x * scale_factor + padding), int(self.start_y * scale_factor + padding)]
        self.car_angle_rad = np.deg2rad(self.start_orientation)

        # Create a surface to represent the map (not displayed directly)
        self.map = pygame.Surface((final_width, final_height))

        # Fill background with white
        self.map.fill(params.white)

        # Calculate position to center the image with padding
        x_offset = (final_width - new_width) // 2
        y_offset = (final_height - new_height) // 2

        # Scale the image and draw it on the surface
        self.external_map = pygame.transform.scale(self.external_map, (new_width, new_height))
        self.map.blit(self.external_map, (x_offset, y_offset))
        
        # Set the window caption (will be used by the display class)
        pygame.display.set_caption(f"Simulation - Map: {map_name}")

    def load_metadata(self, map_name):
        """
        Loads starting position from metadata.
        
        :param map_name: str - Map file name.
        """
        metadata_path = os.path.join("tracks", f"{map_name.split('.')[0]}_metadata.txt")
        self.start_x, self.start_y, self.start_orientation = None, None, None
        
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as file:
                for line in file:
                    if line.startswith("start_line"):
                        _, coords = line.strip().split(": ")
                        self.start_x, self.start_y, self.start_orientation = coords.split(",")
                        self.start_x, self.start_y = int(self.start_x), int(self.start_y) 
                        if self.start_orientation:
                            self.start_orientation = 0
                        else:
                            self.start_orientation = 90
                        break
    
    def move_car(self, cmd_forward, cmd_turn, point_representation=False):
        """
        Moves the car based on commands and map limits.
        Checks collisions with walls based on representation mode.

        :param cmd_forward: int - Movement command forward/backward (-1, 0, 1)
        :param cmd_turn: int - Rotation command left/right (-1, 0, 1)
        :param point_representation: bool - If True, treat car as a point, otherwise as rectangle
        :return: bool - True if movement occurred, False otherwise
        """
        # Flag to track if movement occurred
        has_moved = False

        # Store current position and angle to restore in case of collision
        original_position = self.car_position.copy()
        original_angle = self.car_angle_rad

        # Handle rotation first - always allow rotation even when stuck
        if cmd_turn != 0:
            new_angle = self.car_angle_rad + cmd_turn * self.rotation_speed
            
            # Store current position and angle
            temp_pos = self.car_position.copy()
            temp_angle = self.car_angle_rad
            
            # Try rotating without moving
            self.car_angle_rad = new_angle
            
            # Check if rotation alone causes collision - only matters for rectangle mode
            if not point_representation and self.check_rectangle_collision(point_representation):
                # If rotating in place causes collision, try small backup to free the car
                backup_distance = 2.0  # Small backup distance
                
                # Try backing up slightly in the opposite direction
                backup_x = temp_pos[0] - cmd_forward * np.cos(temp_angle) * backup_distance
                backup_y = temp_pos[1] + cmd_forward * np.sin(temp_angle) * backup_distance
                
                self.car_position = [backup_x, backup_y]
                
                # If still colliding, restore original values
                if self.check_rectangle_collision(point_representation):
                    self.car_position = temp_pos
                    self.car_angle_rad = temp_angle
                else:
                    has_moved = True
            else:
                has_moved = True

        # Update position
        if cmd_forward != 0:
            # Calculate new position based on direction and speed
            new_x = self.car_position[0] + cmd_forward * np.cos(self.car_angle_rad) * self.speed
            new_y = self.car_position[1] - cmd_forward * np.sin(self.car_angle_rad) * self.speed

            # Limit position to map size
            if self.view_width > 0 and self.view_height > 0:
                new_x = max(0, min(new_x, self.view_width - 1))
                new_y = max(0, min(new_y, self.view_height - 1))

            # Store position before moving
            temp_pos = self.car_position.copy()
            
            # Update position temporarily
            self.car_position = [new_x, new_y]
            
            # Check collision with walls
            if self.check_rectangle_collision(point_representation):
                # Collision detected, restore original position
                self.car_position = temp_pos
                
                # Only try to slide along walls in rectangle mode
                if not point_representation:
                    # Try to slide along walls (wall following behavior)
                    # Try moving only in X direction
                    self.car_position = [new_x, temp_pos[1]]
                    if not self.check_rectangle_collision(point_representation):
                        has_moved = True
                    else:
                        # If X movement fails, restore and try Y movement
                        self.car_position = [temp_pos[0], new_y]
                        if not self.check_rectangle_collision(point_representation):
                            has_moved = True
                        else:
                            # If both fail, completely restore position
                            self.car_position = temp_pos
                else:
                    # In point mode, just stay at original position
                    self.car_position = temp_pos
            else:
                # No collision, movement successful
                has_moved = True

        return has_moved

    def check_rectangle_collision(self, point_representation=False):
        """
        Checks if the car collides with walls (black pixels) considering its shape.
        
        :param point_representation: bool - If True, treat car as a point, otherwise as rectangle
        :return: bool - True if collision detected, False otherwise
        """
        if point_representation:
            # Simplified collision detection - just check the center point
            return self.check_collision(int(self.car_position[0]), int(self.car_position[1]))
        else:
            # Full rectangle collision detection
            # Get car corners in global coordinates
            corners = self.car.get_corners(self.car_position, self.car_angle_rad)
            
            # Check perimeter points
            num_perimeter_points = 20  # Number of points to check around perimeter
            
            # Check each corner for collision
            for corner in corners:
                if self.check_collision(int(corner[0]), int(corner[1])):
                    return True
            
            # Check additional points along the perimeter
            for i in range(len(corners)):
                start = corners[i]
                end = corners[(i + 1) % len(corners)]  # Wrap around to first corner
                
                for j in range(1, num_perimeter_points - 1):
                    # Interpolate between corners
                    t = j / (num_perimeter_points - 1)
                    point_x = int(start[0] * (1 - t) + end[0] * t)
                    point_y = int(start[1] * (1 - t) + end[1] * t)
                    
                    if self.check_collision(point_x, point_y):
                        return True
            
            # No collision detected
            return False

    def check_collision(self, x, y):
        """
        Checks if there's a collision with walls (black pixels) at position (x, y).

        :param x: int - X coordinate to check
        :param y: int - Y coordinate to check
        :return: bool - True if collision, False otherwise
        """
        try:
            # Get pixel color at position
            color = self.original_map.get_at((int(x), int(y)))
        
            # Consider collision if pixel is black (wall)
            return (color[0], color[1], color[2]) == (0, 0, 0)  # RGB black
        except IndexError:
            # Out of map bounds, consider as collision
            return True
    
    def polar2cartesian(self, distance, angle):
        """
        Converts polar coordinates to Cartesian in the global system.
        
        :param distance: float - Distance of the point
        :param angle: float - Global angle in radians
        :return: tuple - Coordinates (x, y) in global system
        """
        x = int(distance * np.cos(angle) + self.car_position[0])
        y = int(-distance * np.sin(angle) + self.car_position[1])
        return (x, y)
    
    def data_storage(self, sensor_data):
        """
        Stores sensor data in global coordinates.
        
        :param sensor_data: list - LIDAR sensor data.
        """
        if sensor_data:
            for data_dist, data_ang, _ in sensor_data:
                # Convert polar coordinates to global Cartesian
                point = self.polar2cartesian(data_dist, data_ang)
                self.global_point_cloud.append(point)
    
    def update(self, cmd_forward, cmd_turn, point_representation=False):
        """
        Updates the environment state based on commands.
        
        :param cmd_forward: int - Forward/backward command (-1, 0, 1)
        :param cmd_turn: int - Turn command (-1, 0, 1)
        :param point_representation: bool - If True, treat car as a point, otherwise as rectangle
        :return: bool - True if car moved, False otherwise
        """
        # Move the car based on commands
        moved = self.move_car(cmd_forward, cmd_turn, point_representation)
        
        if moved:
            # Update car sensors, passing position and angle maintained by environment
            sensor_data = self.car.update_sensors(
                self.original_map, 
                self.car_position, 
                self.car_angle_rad
            )
            
            # Store data in global coordinates for visualization
            self.data_storage(sensor_data)
            
        return moved
    
    def run(self, show_global_view=False):
        """
        Sets up the environment and launches the simulation with display.
        
        :param show_global_view: bool - Whether to show the global point cloud view
        """
        # Import here to avoid circular imports
        from display import Display
        
        # Create display handler
        display = Display(self, show_global_view)
        
        # Run the simulation loop
        display.run_simulation()