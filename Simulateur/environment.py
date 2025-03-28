import pygame
import numpy as np
import params
import os 
import time
from car import Car

class Environment:
    def __init__(self, map_name, max_size=500, padding_percent=0.05, show_global_view=True):
        """
        Initializes the simulation environment.

        :param map_name: str - Name of the map file inside 'tracks/' folder.
        :param max_size: int - Maximum size (either width or height).
        :param padding_percent: float - Percentage of max_size to be used as padding.
        :param show_global_view: bool - If True, shows global view map with point cloud.
        """
        pygame.init()
        
        # Visualization parameters
        self.show_global_view = show_global_view
        
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
        
    def format_map(self, map_name, max_size, padding_percent):
        """
        Formats the map for display on screen.
        
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

        # Create window
        pygame.display.set_caption(f"Simulation - Map: {map_name}")
        self.map = pygame.display.set_mode((final_width, final_height))

        # Fill background with white
        self.map.fill(params.white)

        # Calculate position to center the image with padding
        x_offset = (final_width - new_width) // 2
        y_offset = (final_height - new_height) // 2

        # Scale the image and draw it on the screen
        self.external_map = pygame.transform.scale(self.external_map, (new_width, new_height))
        self.map.blit(self.external_map, (x_offset, y_offset))

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
        # print(f"Loaded start position: ({self.start_x}, {self.start_y}, {self.start_orientation})")
    
    def move_car(self, cmd_forward, cmd_turn, map_width, map_height):
        """
        Moves the car based on commands and map limits.
        Checks collisions with walls treating the car as a rectangle.

        :param cmd_forward: int - Movement command forward/backward (-1, 0, 1)
        :param cmd_turn: int - Rotation command left/right (-1, 0, 1)
        :param map_width: int - Map width for boundaries
        :param map_height: int - Map height for boundaries
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
            
            # Check if rotation alone causes collision
            if self.check_rectangle_collision():
                # If rotating in place causes collision, try small backup to free the car
                backup_distance = 2.0  # Small backup distance
                
                # Try backing up slightly in the opposite direction
                backup_x = temp_pos[0] - cmd_forward * np.cos(temp_angle) * backup_distance
                backup_y = temp_pos[1] + cmd_forward * np.sin(temp_angle) * backup_distance
                
                self.car_position = [backup_x, backup_y]
                
                # If still colliding, restore original values
                if self.check_rectangle_collision():
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
            if map_width > 0 and map_height > 0:
                new_x = max(0, min(new_x, map_width - 1))
                new_y = max(0, min(new_y, map_height - 1))

            # Store position before moving
            temp_pos = self.car_position.copy()
            
            # Update position temporarily
            self.car_position = [new_x, new_y]
            
            # Check collision with walls considering car dimensions
            if self.check_rectangle_collision():
                # Collision detected, restore original position
                self.car_position = temp_pos
                
                # Try to slide along walls (wall following behavior)
                # Try moving only in X direction
                self.car_position = [new_x, temp_pos[1]]
                if not self.check_rectangle_collision():
                    has_moved = True
                else:
                    # If X movement fails, restore and try Y movement
                    self.car_position = [temp_pos[0], new_y]
                    if not self.check_rectangle_collision():
                        has_moved = True
                    else:
                        # If both fail, completely restore position
                        self.car_position = temp_pos
            else:
                # No collision, movement successful
                has_moved = True

        return has_moved

    def check_rectangle_collision(self):
        """
        Checks if the car collides with walls (black pixels) considering its rectangular shape.
        
        :return: bool - True if collision detected, False otherwise
        """
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
        if self.show_global_view and sensor_data:
            for data_dist, data_ang, _ in sensor_data:
                # Convert polar coordinates to global Cartesian
                point = self.polar2cartesian(data_dist, data_ang)
                self.global_point_cloud.append(point)
    
    def show_sensor_data(self):
        """Displays sensor data on the map."""
        if self.show_global_view:
            for point in self.global_point_cloud:
                try:
                    self.infomap.set_at((int(point[0]), int(point[1])), params.red)
                except IndexError:
                    # Ignore points outside map boundaries
                    pass

    def create_local_view(self):
        """
        Creates a local view of the point cloud aligned with the front of the car.
        The front of the car always points upward in the local view.
        
        :return: pygame.Surface - Surface with local visualization
        """
        # Create a surface of the same size as other views
        local_view = pygame.Surface((self.view_width, self.view_height))
        local_view.fill(params.black)
        
        # Define center of visualization
        center_x = self.view_width // 2
        center_y = self.view_height // 2
        
        # Draw reference grid
        grid_size = 40  # Size of grid cells
        grid_lines = max(self.view_width, self.view_height) // grid_size + 1
        
        # Grid lines
        for i in range(-grid_lines // 2, grid_lines // 2 + 1):
            # Horizontal lines
            pygame.draw.line(
                local_view, params.gray, 
                (0, center_y + i * grid_size), 
                (self.view_width, center_y + i * grid_size), 
                1
            )
            # Vertical lines
            pygame.draw.line(
                local_view, params.gray, 
                (center_x + i * grid_size, 0), 
                (center_x + i * grid_size, self.view_height), 
                1
            )
        
        # Center lines (representing x and y axes) - thicker
        pygame.draw.line(local_view, params.white, (0, center_y), (self.view_width, center_y), 2)
        pygame.draw.line(local_view, params.white, (center_x, 0), (center_x, self.view_height), 2)
        
        # Draw the vehicle at the center (a rectangle)
        car_width = self.car.width
        car_height = self.car.height
        vehicle_rect = pygame.Rect(
            center_x - car_width // 2, 
            center_y - car_height // 2,
            car_width, 
            car_height
        )
        pygame.draw.rect(local_view, params.green, vehicle_rect)
        
        # Draw a triangle to indicate front of the car
        pygame.draw.polygon(
            local_view, 
            params.blue, 
            [
                (center_x, center_y - car_height // 2 - 5),  # Front tip
                (center_x - 5, center_y - car_height // 2),  # Left corner
                (center_x + 5, center_y - car_height // 2)   # Right corner
            ]
        )
        
        # Draw concentric circles to indicate distance
        for radius in range(grid_size, 6 * grid_size, grid_size):
            pygame.draw.circle(local_view, params.dark_gray, (center_x, center_y), radius, 1)
        
        # Get car's local point cloud
        local_points = self.car.get_local_point_cloud()
        
        # Draw the point cloud - CORRECTION:
        # Transformation to screen coordinates:
        # 1. In local point cloud: x+ is forward, y+ is left
        # 2. In visualization: up is car's front (-y on screen), right is car's right (+x on screen)
        scale_factor = 1.4  # Visualization adjustment
        for local_x, local_y in local_points:
            # Transform coordinates for visualization:
            # Point cloud x-axis (forward) maps to -y on screen (upward)
            # Point cloud y-axis (left) maps to -x on screen (left)
            screen_x = int(center_x - local_y * scale_factor)  # Inverted to fix mirroring
            screen_y = int(center_y - local_x * scale_factor)  # Front always upward
            
            if 0 <= screen_x < self.view_width and 0 <= screen_y < self.view_height:
                # Draw a small circle for better visibility
                pygame.draw.circle(local_view, params.red, (screen_x, screen_y), 2)
        
        # Display current angle on screen
        font = pygame.font.SysFont('Arial', 14)
        angle_text = font.render(f"Angle: {np.rad2deg(self.car_angle_rad):.2f}°", True, params.white)
        local_view.blit(angle_text, (10, 10))
        
        # Display car dimensions on screen
        dimensions_text = font.render(f"Car: {self.car.width}x{self.car.height} px", True, params.white)
        local_view.blit(dimensions_text, (10, 30))
        
        # Identify cardinal directions for easier orientation
        directions = [
            {"text": "Front", "pos": (center_x, 10), "anchor": "center"},
            {"text": "Back", "pos": (center_x, self.view_height - 20), "anchor": "center"},
            {"text": "Left", "pos": (10, center_y), "anchor": "left"},
            {"text": "Right", "pos": (self.view_width - 10, center_y), "anchor": "right"}
        ]
        
        for direction in directions:
            direction_text = font.render(direction["text"], True, params.white)
            text_rect = direction_text.get_rect()
            
            if direction["anchor"] == "center":
                text_rect.centerx = direction["pos"][0]
                text_rect.y = direction["pos"][1]
            elif direction["anchor"] == "left":
                text_rect.x = direction["pos"][0]
                text_rect.centery = direction["pos"][1]
            elif direction["anchor"] == "right":
                text_rect.right = direction["pos"][0]
                text_rect.centery = direction["pos"][1]
                
            local_view.blit(direction_text, text_rect)
        
        return local_view

    def run(self):
        """Main loop to keep the window open and run the simulation."""
        # Create a copy of the original map for collision detection
        # Important: keep the original map without car drawings for collision detection
        self.original_map = self.map.copy()
        
        # Initialize the car (with dimensions)
        self.car = Car(env_map=self.original_map, width=10, height=20)
        
        running = True
    
        # Determine the number of visualization panels based on parameter
        num_panels = 3 if self.show_global_view else 2
        
        # Create a screen suitable for the number of panels
        width, height = self.map.get_width(), self.map.get_height()
        combined_surface = pygame.display.set_mode((width * num_panels, height))
    
        # Initialize `infomap` as a completely black map
        self.map.fill(params.black)
        self.infomap = self.map.copy()
        
        # Clear point cloud at start
        self.global_point_cloud = []
        
        # Draw a legend or instructions
        font = pygame.font.SysFont('Arial', 12)
        controls_text = [
            "Controls:",
            "W - Move forward",
            "S - Move backward",
            "A - Turn left",
            "D - Turn right"
        ]
    
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
    
            # Capture pressed keys
            keys = pygame.key.get_pressed()
    
            # Process keyboard commands
            cmd_forward = 0  # -1: backward, 0: stopped, 1: forward
            cmd_turn = 0     # -1: right, 0: straight, 1: left
            
            if keys[pygame.K_w]:
                cmd_forward = 1
            elif keys[pygame.K_s]:
                cmd_forward = -1
                
            if keys[pygame.K_a]:
                cmd_turn = 1  # Left (counter-clockwise)
            elif keys[pygame.K_d]:
                cmd_turn = -1  # Right (clockwise)
            
            # Environment moves the car based on commands
            moved = self.move_car(
                cmd_forward=cmd_forward, 
                cmd_turn=cmd_turn,
                map_width=width,
                map_height=height
            )
            
            if moved:
                # Update car sensors, passing position and angle maintained by environment
                sensor_data = self.car.update_sensors(
                    self.original_map, 
                    self.car_position, 
                    self.car_angle_rad
                )
                
                # Store data in global coordinates for visualization
                self.data_storage(sensor_data)
                
                # Update visualization
                self.show_sensor_data()
    
            # Create copy of original map to draw the car
            original_with_car = self.original_map.copy()
            
            # Draw the car as a rectangle
            self.draw_car_rectangle(original_with_car, self.car_position, self.car_angle_rad, self.car.width, self.car.height)
            
            # Draw instructions
            y_offset = 10
            for text in controls_text:
                text_surface = font.render(text, True, params.black)
                original_with_car.blit(text_surface, (10, y_offset))
                y_offset += 15
            
            # Create local view
            local_view = self.create_local_view()
    
            # Render visualization panels
            if self.show_global_view:
                # Three panels: original map, infomap and local view
                combined_surface.blit(original_with_car, (0, 0))
                combined_surface.blit(self.infomap, (width, 0))
                combined_surface.blit(local_view, (width * 2, 0))
            else:
                # Two panels: original map and local view
                combined_surface.blit(original_with_car, (0, 0))
                combined_surface.blit(local_view, (width, 0))
    
            # Update screen
            pygame.display.flip()
    
            time.sleep(0.01)
    
        pygame.quit()
    
    def draw_car_rectangle(self, surface, position, angle, width, height, color=params.red):
        """
        Draws the car as a rectangle with orientation at the specified position.
        
        :param surface: pygame.Surface - Surface to draw the car on.
        :param position: tuple - (x, y) Center position of the car.
        :param angle: float - Rotation angle of the car in radians.
        :param width: int - Width of the car.
        :param height: int - Height of the car.
        :param color: tuple - Color of the car (RGB).
        """
        # Get corners using the car's method
        corners = self.car.get_corners(position, angle)
        
        # Draw rectangle
        pygame.draw.polygon(surface, color, corners)
        
        # Draw a small triangle at the front to indicate direction
        front_center = ((corners[0][0] + corners[1][0]) / 2, (corners[0][1] + corners[1][1]) / 2)
        direction_indicator = [
            front_center,  # Front center
            (corners[0][0], corners[0][1]),  # Front-right
            (corners[1][0], corners[1][1])   # Front-left
        ]
        pygame.draw.polygon(surface, params.blue, direction_indicator)
    
    def draw_arrow(self, surface, position, angle, size=10, color=params.red):
        """
        Draws an arrow at the specified position and orientation.
        
        :param surface: pygame.Surface - Surface to draw the arrow on.
        :param position: tuple - (x, y) Center position of the arrow.
        :param angle: float - Rotation angle of the arrow in radians.
        :param size: int - Size of the arrow.
        :param color: tuple - Color of the arrow (RGB).
        """
        x, y = position
        cos_a, sin_a = np.cos(angle), np.sin(angle)

        # Front point of the arrow
        tip = (x + 1.5*size * cos_a, y - 1.5*size * sin_a)

        # Rear points of the arrow (left and right)
        left = (x - 0.5*size * cos_a + 0.5*size * sin_a, y + 0.5*size * sin_a + 0.5*size * cos_a)
        right = (x - 0.5*size * cos_a - 0.5*size * sin_a, y + 0.5*size * sin_a - 0.5*size * cos_a)

        # Draw a triangle representing the arrow
        pygame.draw.polygon(surface, color, [tip, left, right])