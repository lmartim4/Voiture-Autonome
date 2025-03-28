import pygame
import numpy as np

class Lidar:
    def __init__(self, max_range, scan_speed, uncertainty):
        """
        Initializes the LIDAR sensor.
        
        :param max_range: int - Maximum range of the LIDAR in pixels
        :param scan_speed: int - Scan speed (not currently used)
        :param uncertainty: tuple - LIDAR uncertainty in (distance, angle)
        """
        # LIDAR parameters
        self.max_range = max_range
        self.scan_speed = scan_speed  # Not used, but kept for compatibility
        
        # Uncertainty parameters
        self.uncertainty = np.array(uncertainty)
        
        # Scan settings
        self.angular_resolution = 60  # Number of samples per scan
        self.interpolation_steps = 100  # Number of steps for ray casting
    
    def distance(self, point1, point2):
        """
        Calculates the Euclidean distance between two points.
        
        :param point1: tuple - Coordinates (x, y) of the first point
        :param point2: tuple - Coordinates (x, y) of the second point
        :return: float - Distance between points
        """
        px = point2[0] - point1[0]
        py = point2[1] - point1[1]
        return np.sqrt(px**2 + py**2)
    
    def add_uncertainty(self, distance, angle):
        """
        Adds uncertainty to distance and angle values.
        
        :param distance: float - Measured distance
        :param angle: float - Measured angle in radians
        :return: list - [distance with noise, angle with noise]
        """
        mean = np.array([distance, angle])
        covariance = np.diag(self.uncertainty ** 2)
        
        # Add Gaussian noise
        distance, angle = np.random.multivariate_normal(mean, covariance)
        
        # Ensure positive distance
        distance = max(distance, 0)
        
        return [distance, angle]
    
    def sense_obstacles(self, env_map, car_position, car_angle):
        """
        Detects obstacles using ray casting from given position and angle.
        
        :param env_map: pygame.Surface - Environment map for detection
        :param car_position: tuple/list - Car position (x, y) on the map
        :param car_angle: float - Car angle in radians
        :return: list - List of measurements [distance, angle, position] or False if empty
        """
        # Get map dimensions
        map_width, map_height = env_map.get_width(), env_map.get_height()
        
        data = []
        x_global, y_global = car_position

        # Scan in an arc from -90° to +90° in front of the car
        for angle in np.linspace(-np.pi/2, np.pi/2, self.angular_resolution, False):
            # Global ray angle
            angle_scan = car_angle + angle
            
            # Ray endpoint (considering maximum range)
            x_scan = x_global + self.max_range * np.cos(angle_scan)
            y_scan = y_global - self.max_range * np.sin(angle_scan)

            # Ray casting - linear interpolation between car position and endpoint
            for i in range(0, self.interpolation_steps):
                # Linear interpolation
                u = i / self.interpolation_steps
                x = int(u * x_scan + (1-u) * x_global)
                y = int(u * y_scan + (1-u) * y_global)

                # Check if point is within map boundaries
                if 0 <= x < map_width and 0 <= y < map_height:
                    # Check if point is an obstacle (black pixel)
                    color = env_map.get_at((x, y))
                    
                    # Consider obstacle if pixel is black
                    if (color[0], color[1], color[2]) == (0, 0, 0):  # Black
                        # Calculate distance to obstacle
                        distance = self.distance((x_global, y_global), (x, y))
                        
                        # Add uncertainty to measurements
                        output = self.add_uncertainty(distance, angle_scan)
                        
                        # Add origin position for reference (used by environment)
                        output.append(car_position)
                        
                        # Add to data list
                        data.append(output)
                        
                        # Stop ray casting at this angle, already found obstacle
                        break
        
        # Return data if it exists, False otherwise
        return data if len(data) > 0 else False