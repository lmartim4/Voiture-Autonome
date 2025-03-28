import numpy as np
from lidar import Lidar

class Car:
    def __init__(self, env_map, width=10, height=20, max_lidar_range=200, lidar_speed=4, lidar_uncertainty=(0.5, 0.01)):
        """
        Initializes the car with its sensors and dimensions.
        
        :param env_map: pygame.Surface - Reference to the map for sensing
        :param width: int - Width of the car in pixels
        :param height: int - Height of the car in pixels
        :param max_lidar_range: int - Maximum LIDAR range
        :param lidar_speed: int - LIDAR scan speed
        :param lidar_uncertainty: tuple - LIDAR uncertainty in (distance, angle)
        """
        # Car dimensions
        self.width = width
        self.height = height
        
        # Initialize LIDAR
        self.lidar = Lidar(max_lidar_range, lidar_speed, lidar_uncertainty)
        
        # Store the local point cloud
        self.local_point_cloud = []
        
    def update_sensors(self, env_map, position, angle_rad):
        """
        Updates the car's sensors (LIDAR) based on the environment map.
        
        :param env_map: pygame.Surface - Current environment map
        :param position: tuple/list - Current car position (x,y)
        :param angle_rad: float - Current car angle in radians
        :return: list - LIDAR data if exists, False otherwise
        """
        # Collect LIDAR data
        sensor_data = self.lidar.sense_obstacles(env_map, position, angle_rad)
        
        # Clear previous local point cloud
        self.local_point_cloud = []
        
        # Process sensor data to store locally
        if sensor_data:
            for data_dist, data_ang, _ in sensor_data:
                # Calculate relative angle to the front of the car
                rel_angle = data_ang - angle_rad
                
                # Local Cartesian coordinates
                # In car's local system: 
                # - x positive is forward (angle 0)
                # - y positive is to the left (angle +90°)
                local_x = data_dist * np.cos(rel_angle)
                local_y = data_dist * np.sin(rel_angle)
                
                self.local_point_cloud.append((local_x, local_y))
                
        return sensor_data
    
    def get_local_point_cloud(self):
        """Returns the point cloud in local car coordinates."""
        return self.local_point_cloud
        
    def get_corners(self, position, angle_rad):
        """
        Calculates the four corners of the car based on its position and orientation.
        
        :param position: tuple - (x, y) center position of the car
        :param angle_rad: float - orientation angle in radians
        :return: list - four corner points [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        """
        x, y = position
        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
        
        # Calculate half-dimensions for convenience
        half_width = self.width / 2
        half_height = self.height / 2
        
        # Calculate corner offsets from center (local coordinates)
        # The order is: front-right, front-left, rear-left, rear-right
        local_corners = [
            (half_height, -half_width),    # Front-right
            (half_height, half_width),     # Front-left
            (-half_height, half_width),    # Rear-left
            (-half_height, -half_width)    # Rear-right
        ]
        
        # Transform to global coordinates with rotation
        global_corners = []
        for local_x, local_y in local_corners:
            # Apply rotation and translation
            corner_x = x + (local_x * cos_a - local_y * sin_a)
            corner_y = y - (local_x * sin_a + local_y * cos_a)
            global_corners.append((corner_x, corner_y))
            
        return global_corners