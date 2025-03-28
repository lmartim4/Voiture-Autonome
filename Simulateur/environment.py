import pygame
import numpy as np
import params
import os 
import time

class Environment:
    
    def __init__(self, map_name, speed_ms =2.5, rotation_speed_deg=3, max_size=500, padding_percent=0.05):
        """
        Initializes the simulation environment.

        :param map_name: str, Name of the map file inside 'tracks/' folder.
        :param max_size: int, Maximum size (either width or height).
        :param padding_percent: float, Percentage of the max_size to be used as padding.
        """
        pygame.init()
        self.speed = speed_ms  # Velocidade de movimento
        self.rotation_speed = np.deg2rad(rotation_speed_deg)  # Velocidade de rotação (graus)

        # Point cloud data to be draw
        self.pointCloud = []

        # Load external map
        self.external_map = pygame.image.load(f'tracks/{map_name}')
        
        # Load metadata for starting position
        self.load_metadata(map_name)

        # Format the map
        self.format_map(map_name, max_size, padding_percent)
        
    def format_map(self, map_name, max_size, padding_percent):
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
        
        self.start_x = int(self.start_x * scale_factor + padding)
        self.start_y = int(self.start_y * scale_factor + padding)

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

    def load_metadata(self, map_name):
        """Loads the start position from the metadata file."""
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
        print(f"Loaded start position: ({self.start_x}, {self.start_y}, {self.start_orientation})")

    def polar2cartesian(self, distance, angle, position):
        x = int(distance * np.cos(angle) + position[0])
        y = int(-distance * np.sin(angle) + position[1])
        return (x,y)
    
    def data_storage(self,data):
        # print(len(self.pointCloud))
        if data:
            for data_dist, data_ang, data_pos in data:
                point = self.polar2cartesian(data_dist, data_ang, data_pos)
                # if point not in self.pointCloud : 
                self.pointCloud.append(point)
    
    def show_sensor_data(self):
        # self.infomap = self.map.copy()

        for point in self.pointCloud:
            self.infomap.set_at((point[0], point[1]),params.red)

    def run(self):
        """Main loop to keep the window open."""
        running = True

        # Criar uma nova tela com o dobro da largura para exibir os mapas lado a lado
        width, height = self.map.get_width(), self.map.get_height()
        combined_surface = pygame.display.set_mode((width * 2, height))

        # Inicializar `infomap` como um mapa completamente preto
        self.infomap.fill(params.black)  

        position = [self.start_x, self.start_y]
        angle_rad = np.deg2rad(self.start_orientation)

        while running:
            sensorON = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Capturar teclas pressionadas
            keys = pygame.key.get_pressed()

            # Definir um novo ponto de posição temporário
            new_x, new_y = position[0], position[1]

            angle_cmd = True
            if keys[pygame.K_a]:  # Rotaciona para esquerda
                angle_rad += self.rotation_speed 
            elif keys[pygame.K_d]:  # Rotaciona para direita
                angle_rad -= self.rotation_speed
            else:
                angle_cmd = False

            speed_cmd = True
            # Movimento para frente (W) e para trás (S)
            if keys[pygame.K_w]:  # Avança
                new_x = int(position[0] + np.cos(angle_rad) * self.speed)
                new_y = int(position[1] - np.sin(angle_rad) * self.speed)

            elif keys[pygame.K_s]:  # Recuar
                new_x = int(position[0] - np.cos(angle_rad) * self.speed)
                new_y = int(position[1] + np.sin(angle_rad) * self.speed)
            else:
                speed_cmd = False
            

            sensorON = speed_cmd or angle_cmd 

            # **Impedir valores negativos (manter dentro dos limites da tela)**
            new_x = max(0, min(new_x, width - 1))
            new_y = max(0, min(new_y, height - 1))

            # Atualizar `position`
            position = [new_x, new_y]

            if sensorON:
                self.lidar.position = position
                self.lidar.angle_rad = angle_rad
                # print(f"Posição: {position}, Ângulo: {np.rad2deg(angle_rad)}°")  # Para debug
                sensor_data = self.lidar.sense_obstacles()
                self.data_storage(sensor_data)
                self.show_sensor_data()

            # Criar cópia do mapa original para desenhar o carro
            original_with_car = self.original_map.copy()
            self.draw_arrow(original_with_car, position, angle_rad, size=8, color=params.red)


            # **Desenhar o mapa original na esquerda**
            combined_surface.blit(original_with_car, (0, 0))

            # **Desenhar o infomap atualizado na direita**
            combined_surface.blit(self.infomap, (width, 0))

            # Atualizar a tela
            pygame.display.flip()

            time.sleep(0.01)

        pygame.quit()
    
    def draw_arrow(self,surface, position, angle, size=10, color=params.red):
        """
        Desenha uma seta na posição e orientação especificadas.

        :param surface: pygame.Surface - Superfície onde desenhar a seta.
        :param position: tuple - (x, y) Posição central da seta.
        :param angle: float - Ângulo de rotação da seta em radianos.
        :param size: int - Tamanho da seta.
        :param color: tuple - Cor da seta (RGB).
        """
        x, y = position
        cos_a, sin_a = np.cos(angle), np.sin(angle)

        # Ponto da frente da seta
        tip = (x + 1.5*size * cos_a, y - 1.5*size * sin_a)

        # Pontos traseiros da seta (esquerda e direita)
        left = (x - 0.5*size * cos_a + 0.5*size * sin_a, y + 0.5*size * sin_a + 0.5*size * cos_a)
        right = (x - 0.5*size * cos_a - 0.5*size * sin_a, y + 0.5*size * sin_a - 0.5*size * cos_a)

        # Desenhar um triângulo representando a seta
        pygame.draw.polygon(surface, color, [tip, left, right])


