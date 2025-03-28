import pygame
import numpy as np
import params
import time

class Display:
    def __init__(self, environment, show_global_view=True, show_point_car=False):
        """
        Initializes the display for the simulation environment.
        
        :param environment: Environment - The environment to display
        :param show_global_view: bool - If True, shows global view map with point cloud
        :param show_point_car: bool - If True, shows car as a point, otherwise as a rectangle
        """
        self.environment = environment
        self.show_global_view = show_global_view
        self.show_point_car = show_point_car
        
        # Get dimensions from environment
        self.view_width = environment.view_width
        self.view_height = environment.view_height
        
        # Initialize display components
        self.initialize_display()
        
    def initialize_display(self):
        """
        Initializes the display components based on the environment.
        """
        # Determine the number of visualization panels based on parameter
        num_panels = 3 if self.show_global_view else 2
        
        # Create a screen suitable for the number of panels
        width, height = self.view_width, self.view_height
        self.combined_surface = pygame.display.set_mode((width * num_panels, height))
        
        # Create infomap for point cloud visualization
        self.infomap = pygame.Surface((width, height))
        self.infomap.fill(params.black)
        
        # Initialize font for text rendering
        self.font = pygame.font.SysFont('Arial', 12)
        self.controls_text = [
            "Controls:",
            "W - Move forward",
            "S - Move backward",
            "A - Turn left",
            "D - Turn right",
            "P - Toggle car representation"
        ]
    
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
        corners = self.environment.car.get_corners(position, angle)
        
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
        
    def show_sensor_data(self):
        """
        Displays global point cloud sensor data on the infomap.
        """
        if self.show_global_view:
            for point in self.environment.global_point_cloud:
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
        
        car_width = self.environment.car.width
        car_height = self.environment.car.height
        
        # Draw the vehicle at the center based on the display mode
        if self.show_point_car:
            # Draw the car as an arrow/triangle
            pygame.draw.polygon(
                local_view, 
                params.green, 
                [
                    (center_x, center_y - 10),  # Front tip
                    (center_x - 7, center_y + 5),  # Bottom left
                    (center_x + 7, center_y + 5)   # Bottom right
                ]
            )
        else:
            # Draw the vehicle as a rectangle
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
        local_points = self.environment.car.get_local_point_cloud()
        
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
        angle_text = font.render(f"Angle: {np.rad2deg(self.environment.car_angle_rad):.2f}°", True, params.white)
        local_view.blit(angle_text, (10, 10))
        
        # Display car dimensions on screen
        dimensions_text = font.render(f"Car: {self.environment.car.width}x{self.environment.car.height} px", True, params.white)
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
        
    def update_display(self):
        """
        Updates the display with the current state of the environment.
        """
        # Create copy of original map to draw the car
        original_with_car = self.environment.original_map.copy()
        
        # Draw the car based on the display mode
        if self.show_point_car:
            # Draw the car as a point (arrow)
            self.draw_arrow(
                original_with_car,
                self.environment.car_position,
                self.environment.car_angle_rad,
                size=15,
                color=params.red
            )
        else:
            # Draw the car as a rectangle
            self.draw_car_rectangle(
                original_with_car, 
                self.environment.car_position, 
                self.environment.car_angle_rad, 
                self.environment.car.width, 
                self.environment.car.height
            )
        
        # Draw instructions
        y_offset = 10
        for text in self.controls_text:
            text_surface = self.font.render(text, True, params.black)
            original_with_car.blit(text_surface, (10, y_offset))
            y_offset += 15
        
        # Update point cloud visualization if needed
        self.show_sensor_data()
        
        # Create local view
        local_view = self.create_local_view()

        # Render visualization panels
        if self.show_global_view:
            # Three panels: original map, infomap and local view
            self.combined_surface.blit(original_with_car, (0, 0))
            self.combined_surface.blit(self.infomap, (self.view_width, 0))
            self.combined_surface.blit(local_view, (self.view_width * 2, 0))
        else:
            # Two panels: original map and local view
            self.combined_surface.blit(original_with_car, (0, 0))
            self.combined_surface.blit(local_view, (self.view_width, 0))

        # Update screen
        pygame.display.flip()
        
    def run_simulation(self):
        """
        Main loop to run the simulation and handle display updates.
        """
        running = True
        # Track key states to detect single presses
        key_pressed = {pygame.K_p: False}
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYUP:
                    # Handle key release events
                    if event.key in key_pressed:
                        key_pressed[event.key] = False
    
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
            
            # Toggle car representation with P key (on key press, not hold)
            if keys[pygame.K_p] and not key_pressed[pygame.K_p]:
                self.show_point_car = not self.show_point_car
                key_pressed[pygame.K_p] = True  # Mark key as pressed
            
            # Update environment state based on commands and car representation
            moved = self.environment.update(cmd_forward, cmd_turn, self.show_point_car)
            
            # Update display
            self.update_display()
    
            time.sleep(0.01)
    
        pygame.quit()