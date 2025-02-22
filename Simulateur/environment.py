import pygame
import numpy as np
import params

class Environment:
    
    def __init__(self, map_name, max_size=800, padding_percent=0.05):
        """
        Initializes the simulation environment.

        :param map_name: str, Name of the map file inside 'tracks/' folder.
        :param max_size: int, Maximum size (either width or height).
        :param padding_percent: float, Percentage of the max_size to be used as padding.
        """
        pygame.init()

        # Point cloud data to be draw
        self.pointCloud = []

        # Load external map
        self.external_map = pygame.image.load(f'tracks/{map_name}')

        # Get original dimensions
        self.map_width, self.map_height = self.external_map.get_width(), self.external_map.get_height()

        # Compute the scale factor while keeping aspect ratio
        scale_factor = min(max_size / self.map_width, max_size / self.map_height)

        # Compute new dimensions after scaling
        new_width, new_height = int(self.map_width * scale_factor), int(self.map_height * scale_factor)

        # Compute padding based on max_size and the given percentage
        padding = int(max_size * padding_percent)

        # Compute final window dimensions including padding
        final_width = new_width + 2 * padding
        final_height = new_height + 2 * padding

        # Create window
        pygame.display.set_caption(f"Simulation - Map: {map_name}")
        self.map = pygame.display.set_mode((final_width, final_height))

        # Fill background with white
        self.map.fill(params.white)

        # Compute position to center the image with padding
        x_offset = (final_width - new_width) // 2
        y_offset = (final_height - new_height) // 2

        # Scale the image and draw it on the screen
        self.external_map = pygame.transform.scale(self.external_map, (new_width, new_height))
        self.map.blit(self.external_map, (x_offset, y_offset))

    def polar2cartesian(self, distance, angle, position):
        x = int(distance * np.cos(angle) + position[0])
        y = int(-distance * np.sin(angle) + position[1])
        return (x,y)
    
    def data_storage(self,data):
        # print(len(self.pointCloud))
        if data:
            for data_dist, data_ang, data_pos in data:
                point = self.polar2cartesian(data_dist, data_ang, data_pos)
                if point not in self.pointCloud : 
                    self.pointCloud.append(point)
    
    def show_sensor_data(self):
        self.infomap = self.map.copy()

        for point in self.pointCloud:
            self.infomap.set_at((int(point[0]), int(point[1])),params.red)

    def run(self):
        """Main loop to keep the window open."""
        running = True
        while running:
            sensorON = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if pygame.mouse.get_focused():
                    sensorON = True
                
                # Precisa ?????????
                elif not pygame.mouse.get_focused():
                    sensorON = False
            
            if sensorON: 
                position = pygame.mouse.get_pos()
                self.lidar.position = position
                sensor_data = self.lidar.sense_obstacles()
                self.data_storage(sensor_data)
                self.show_sensor_data()
            
            self.map.blit(self.infomap, (0,0))
            pygame.display.update()


        pygame.quit()
