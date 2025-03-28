import numpy as np
from lidar import Lidar

class Car:
    def __init__(self, env_map, max_lidar_range=200, lidar_speed=4, lidar_uncertainty=(0.5, 0.01)):
        """
        Inicializa o carro com seus sensores.
        
        :param env_map: pygame.Surface - Referência ao mapa para sensing
        :param max_lidar_range: int - Alcance máximo do LIDAR
        :param lidar_speed: int - Velocidade de varredura do LIDAR
        :param lidar_uncertainty: tuple - Incerteza do LIDAR em (distância, ângulo)
        """
        # Inicializar o LIDAR
        self.lidar = Lidar(max_lidar_range, lidar_speed, lidar_uncertainty)
        
        # Armazenar a point cloud local
        self.local_point_cloud = []
        
    def update_sensors(self, env_map, position, angle_rad):
        """
        Atualiza os sensores do carro (LIDAR) baseado no mapa do ambiente.
        
        :param env_map: pygame.Surface - Mapa atual do ambiente
        :param position: tuple/list - Posição atual do carro (x,y)
        :param angle_rad: float - Ângulo atual do carro em radianos
        :return: list - Dados do LIDAR se existirem, False caso contrário
        """
        # Coletar dados do LIDAR
        sensor_data = self.lidar.sense_obstacles(env_map, position, angle_rad)
        
        # Limpar a point cloud local anterior
        self.local_point_cloud = []
        
        # Processar dados do sensor para armazenar localmente
        if sensor_data:
            for data_dist, data_ang, _ in sensor_data:
                # Calcular ângulo relativo em relação à frente do carro
                rel_angle = data_ang - angle_rad
                
                # Coordenadas cartesianas locais
                # No sistema local do carro: 
                # - x positivo é para frente (ângulo 0)
                # - y positivo é para a esquerda (ângulo +90°)
                local_x = data_dist * np.cos(rel_angle)
                local_y = data_dist * np.sin(rel_angle)
                
                self.local_point_cloud.append((local_x, local_y))
                
        return sensor_data
    
    def get_local_point_cloud(self):
        """Retorna a point cloud em coordenadas locais do carro."""
        return self.local_point_cloud