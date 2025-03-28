import pygame
import numpy as np
import params

class Lidar:

    def __init__(self, max_range, lidar_speed, env_map, uncertainty): 
        
        # TODO : colocar speed dentro da parte de sense_obstacles (ta fixo por enquanto em 60 pontos)
        # Lidar parameters 
        self.max_range = max_range
        self.lidar_speed = lidar_speed 

        self.map = env_map
        
        # Sensor measurement noise matrix. Assumes non-correlated noise from distance and angle
        self.sensor_measurement_noise = np.array([uncertainty[0], uncertainty[1]])
        
        # Parameters 
        
        # TODO : colocar isso na classe do CARRINHO, e nao do lidar
        # TODO : colocar carregando do arquivos + convencoes 
        self.position = (0,0)
        self.angle_rad = 0

        self.width, self.height = pygame.display.get_surface().get_size()

        self.sensed_obstacles = []

    def distance(self, obstacle_position):
        px = obstacle_position[0] - self.position[0]
        py = obstacle_position[1] - self.position[1]

        return np.sqrt(px**2 + py**2)
    

    # TODO : modificar a maneira pela qual a incerteza é calculada. Nao acho q faz sentido ruido gaussiano
    # no angulo, dado que no lidar fisico temos o indice com ctz do array. Substituir isso aqui pelas medidas capturadas
    # pela equipe, provavelmente à partir de um arquivo de configuração.
    def uncertainty_add(self, distance, angle):

        mean = np.array([distance, angle])
        covariance = np.diag(self.sensor_measurement_noise ** 2)
        distance, angle = np.random.multivariate_normal(mean, covariance)
        
        # Clip it, in order to not get negative values 
        # TODO : Probably best to revise this, as it doesnt take into account the periodicity 
        # of the angles and any form of jacobian distortion
        distance = max(distance, 0) 

        return [distance, angle]
    
    # LiDAR's counterclockwise motion
    def sense_obstacles(self):

        data = []
        x_global, y_global = self.position[0], self.position[1]

        # linspace from 0 to 2pi, taking 60 samples, not including (False) the endpoint
        for angle in np.linspace(-np.pi/2, np.pi/2,60, False):
            angle_scan = self.angle_rad + angle
            x_scan, y_scan = (x_global + self.max_range * np.cos(angle_scan),
                               y_global - self.max_range * np.sin(angle_scan) )

            interpolation_range = 100
            for i in range(0,interpolation_range): 
                u = i/interpolation_range
                x = int(u * x_scan + (1-u) * x_global)
                y = int(u * y_scan + (1-u) * y_global)

                if 0 < x < self.width and 0 < y < self.height:
                    color = self.map.get_at((x,y))

                    # TODO : Fazer as cores serem globais
                    if (color[0],color[1],color[2]) == params.black:
                        distance = self.distance((x,y))
                        output = self.uncertainty_add(distance, angle_scan)
                        output.append(self.position)
                        
                        data.append(output)

                        # We need to break it as it has already found the wall 
                        break
            
        return data if len(data) > 0 else False
    