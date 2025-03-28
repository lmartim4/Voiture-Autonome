import pygame
import numpy as np

class Lidar:
    def __init__(self, max_range, scan_speed, uncertainty):
        """
        Inicializa o sensor LIDAR.
        
        :param max_range: int - Alcance máximo do LIDAR em pixels
        :param scan_speed: int - Velocidade de scan (não usado atualmente)
        :param uncertainty: tuple - Incerteza do LIDAR em (distância, ângulo)
        """
        # Parâmetros do LIDAR
        self.max_range = max_range
        self.scan_speed = scan_speed  # Não usado, mas mantido para compatibilidade
        
        # Parâmetros de incerteza
        self.uncertainty = np.array(uncertainty)
        
        # Configurações de varredura
        self.angular_resolution = 60  # Número de amostras por varredura
        self.interpolation_steps = 100  # Número de passos para ray casting
    
    def distance(self, point1, point2):
        """
        Calcula a distância euclidiana entre dois pontos.
        
        :param point1: tuple - Coordenadas (x, y) do primeiro ponto
        :param point2: tuple - Coordenadas (x, y) do segundo ponto
        :return: float - Distância entre os pontos
        """
        px = point2[0] - point1[0]
        py = point2[1] - point1[1]
        return np.sqrt(px**2 + py**2)
    
    def add_uncertainty(self, distance, angle):
        """
        Adiciona incerteza aos valores de distância e ângulo.
        
        :param distance: float - Distância medida
        :param angle: float - Ângulo medido em radianos
        :return: list - [distância com ruído, ângulo com ruído]
        """
        mean = np.array([distance, angle])
        covariance = np.diag(self.uncertainty ** 2)
        
        # Adicionar ruído gaussiano
        distance, angle = np.random.multivariate_normal(mean, covariance)
        
        # Garantir distância positiva
        distance = max(distance, 0)
        
        return [distance, angle]
    
    def sense_obstacles(self, env_map, car_position, car_angle):
        """
        Detecta obstáculos usando ray casting a partir da posição e ângulo fornecidos.
        
        :param env_map: pygame.Surface - Mapa do ambiente para detecção
        :param car_position: tuple/list - Posição (x, y) do carro no mapa
        :param car_angle: float - Ângulo do carro em radianos
        :return: list - Lista de medições [distância, ângulo, posição] ou False se vazio
        """
        # Obter dimensões do mapa
        map_width, map_height = env_map.get_width(), env_map.get_height()
        
        data = []
        x_global, y_global = car_position

        # Scan em um arco de -90° a +90° em frente ao carro
        for angle in np.linspace(-np.pi/2, np.pi/2, self.angular_resolution, False):
            # Ângulo global do raio
            angle_scan = car_angle + angle
            
            # Ponto final do raio (considerando alcance máximo)
            x_scan = x_global + self.max_range * np.cos(angle_scan)
            y_scan = y_global - self.max_range * np.sin(angle_scan)

            # Ray casting - interpolação linear entre a posição do carro e o ponto final
            for i in range(0, self.interpolation_steps):
                # Interpolação linear
                u = i / self.interpolation_steps
                x = int(u * x_scan + (1-u) * x_global)
                y = int(u * y_scan + (1-u) * y_global)

                # Verificar se o ponto está dentro dos limites do mapa
                if 0 <= x < map_width and 0 <= y < map_height:
                    # Verificar se o ponto é um obstáculo (pixel preto)
                    color = env_map.get_at((x, y))
                    
                    # Considerar obstáculo se pixel for preto
                    if (color[0], color[1], color[2]) == (0, 0, 0):  # Preto
                        # Calcular distância até o obstáculo
                        distance = self.distance((x_global, y_global), (x, y))
                        
                        # Adicionar incerteza às medições
                        output = self.add_uncertainty(distance, angle_scan)
                        
                        # Adicionar posição de origem para referência (usada pelo ambiente)
                        output.append(car_position)
                        
                        # Adicionar à lista de dados
                        data.append(output)
                        
                        # Parar o ray casting deste ângulo, já encontrou obstáculo
                        break
        
        # Retornar dados se existirem, False caso contrário
        return data if len(data) > 0 else False