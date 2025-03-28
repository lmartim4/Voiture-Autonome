import pygame
import numpy as np
import params
import os 
import time
from car import Car

class Environment:
    def __init__(self, map_name, max_size=500, padding_percent=0.05):

        pygame.init()
        
        # Parâmetros de movimento (mantidos no ambiente)
        self.speed = params.default_speed
        self.rotation_speed = np.deg2rad(params.default_rotation_speed)
        
        # Posição e ângulo do carro (mantidos no ambiente)
        self.car_position = [0, 0]  # Será atualizada após carregar metadados
        self.car_angle_rad = 0      # Será atualizada após carregar metadados
        
        # Point cloud do ambiente (pontos detectados em coordenadas globais)
        self.global_point_cloud = []
        
        # Carregar mapa externo
        self.external_map = pygame.image.load(f'tracks/{map_name}')
        
        # Carregar posição inicial dos metadados
        self.load_metadata(map_name)
        
        # Formatar o mapa
        self.format_map(map_name, max_size, padding_percent)
        
        # Inicializar o carro (sem posição, apenas com sensores)
        self.car = None  # Será inicializado após a criação do mapa original
        
    def format_map(self, map_name, max_size, padding_percent):
        """
        Formata o mapa para exibição na tela.
        
        :param map_name: str - Nome do arquivo do mapa.
        :param max_size: int - Tamanho máximo.
        :param padding_percent: float - Porcentagem de padding.
        """
        # Dimensões originais
        self.map_width, self.map_height = self.external_map.get_width(), self.external_map.get_height()

        # Calcular fator de escala mantendo a proporção
        scale_factor = min(max_size / self.map_width, max_size / self.map_height)

        # Calcular novas dimensões após escala
        new_width, new_height = int(self.map_width * scale_factor), int(self.map_height * scale_factor)

        # Calcular padding com base no tamanho máximo e na porcentagem dada
        padding = int(max_size * padding_percent)

        # Calcular dimensões finais da janela incluindo padding
        final_width = new_width + 2 * padding
        final_height = new_height + 2 * padding
        
        # Armazenar dimensões para uso posterior
        self.view_width = final_width
        self.view_height = final_height
        
        # Ajustar posição inicial com escala e padding
        self.car_position = [int(self.start_x * scale_factor + padding), int(self.start_y * scale_factor + padding)]
        self.car_angle_rad = np.deg2rad(self.start_orientation)

        # Criar janela
        pygame.display.set_caption(f"Simulation - Map: {map_name}")
        self.map = pygame.display.set_mode((final_width, final_height))

        # Preencher background com branco
        self.map.fill(params.white)

        # Calcular posição para centralizar a imagem com padding
        x_offset = (final_width - new_width) // 2
        y_offset = (final_height - new_height) // 2

        # Redimensionar a imagem e desenhá-la na tela
        self.external_map = pygame.transform.scale(self.external_map, (new_width, new_height))
        self.map.blit(self.external_map, (x_offset, y_offset))

    def load_metadata(self, map_name):
        """
        Carrega a posição inicial dos metadados.
        
        :param map_name: str - Nome do arquivo do mapa.
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
        Move o carro com base nos comandos e limites do mapa.
        
        :param cmd_forward: int - Comando de movimento para frente/trás (-1, 0, 1)
        :param cmd_turn: int - Comando de rotação para esquerda/direita (-1, 0, 1)
        :param map_width: int - Largura do mapa para limites
        :param map_height: int - Altura do mapa para limites
        :return: bool - True se houve movimento, False caso contrário
        """
        # Flag para rastrear se houve movimento
        has_moved = False
        
        # Atualizar ângulo
        if cmd_turn != 0:
            self.car_angle_rad += cmd_turn * self.rotation_speed
            has_moved = True
            
        # Atualizar posição
        if cmd_forward != 0:
            new_x = int(self.car_position[0] + cmd_forward * np.cos(self.car_angle_rad) * self.speed)
            new_y = int(self.car_position[1] - cmd_forward * np.sin(self.car_angle_rad) * self.speed)
            
            # Limitar a posição ao tamanho do mapa
            if map_width > 0 and map_height > 0:
                new_x = max(0, min(new_x, map_width - 1))
                new_y = max(0, min(new_y, map_height - 1))
            
            self.car_position = [new_x, new_y]
            has_moved = True
        
        return has_moved
    
    def polar2cartesian(self, distance, angle):
        """
        Converte coordenadas polares para cartesianas no sistema global.
        
        :param distance: float - Distância do ponto
        :param angle: float - Ângulo global do ponto em radianos
        :return: tuple - Coordenadas (x, y) no sistema global
        """
        x = int(distance * np.cos(angle) + self.car_position[0])
        y = int(-distance * np.sin(angle) + self.car_position[1])
        return (x, y)
    
    def data_storage(self, sensor_data):
        """
        Armazena os dados do sensor em coordenadas globais.
        
        :param sensor_data: list - Dados do sensor LIDAR.
        """
        if sensor_data:
            for data_dist, data_ang, _ in sensor_data:
                # Converter coordenadas polares para cartesianas globais
                point = self.polar2cartesian(data_dist, data_ang)
                self.global_point_cloud.append(point)
    
    def show_sensor_data(self):
        """Exibe os dados dos sensores no mapa."""
        for point in self.global_point_cloud:
            try:
                self.infomap.set_at((int(point[0]), int(point[1])), params.red)
            except IndexError:
                # Ignorar pontos que estejam fora dos limites do mapa
                pass

    def create_local_view(self):
        """
        Cria uma visualização local da point cloud alinhada com a frente do carro.
        A frente do carro sempre aponta para cima na visualização local.
        
        :return: pygame.Surface - Superfície com a visualização local.
        """
        # Criar uma superfície do mesmo tamanho que as outras visualizações
        local_view = pygame.Surface((self.view_width, self.view_height))
        local_view.fill(params.black)
        
        # Definir o centro da visualização
        center_x = self.view_width // 2
        center_y = self.view_height // 2
        
        # Desenhar grid de referência
        grid_size = 40  # Tamanho das células da grade
        grid_lines = max(self.view_width, self.view_height) // grid_size + 1
        
        # Linhas de grade
        for i in range(-grid_lines // 2, grid_lines // 2 + 1):
            # Linhas horizontais
            pygame.draw.line(
                local_view, params.gray, 
                (0, center_y + i * grid_size), 
                (self.view_width, center_y + i * grid_size), 
                1
            )
            # Linhas verticais
            pygame.draw.line(
                local_view, params.gray, 
                (center_x + i * grid_size, 0), 
                (center_x + i * grid_size, self.view_height), 
                1
            )
        
        # Linhas de centro (representam os eixos x e y) - mais espessas
        pygame.draw.line(local_view, params.white, (0, center_y), (self.view_width, center_y), 2)
        pygame.draw.line(local_view, params.white, (center_x, 0), (center_x, self.view_height), 2)
        
        # Desenhar o veículo no centro (um pequeno triângulo apontando para cima)
        vehicle_size = 10
        vehicle_points = [
            (center_x, center_y - vehicle_size),  # Ponta (frente do carro)
            (center_x - vehicle_size, center_y + vehicle_size),  # Traseira esquerda
            (center_x + vehicle_size, center_y + vehicle_size)   # Traseira direita
        ]
        pygame.draw.polygon(local_view, params.green, vehicle_points)
        
        # Desenhar círculos concêntricos para indicar distância
        for radius in range(grid_size, 6 * grid_size, grid_size):
            pygame.draw.circle(local_view, params.dark_gray, (center_x, center_y), radius, 1)
        
        # Obter point cloud local do carro
        local_points = self.car.get_local_point_cloud()
        
        # Desenhar os pontos da point cloud - CORREÇÃO:
        # A transformação para a visualização na tela:
        # 1. Na point cloud local: x+ é para frente, y+ é para esquerda
        # 2. Na visualização: para cima é frente do carro (-y na tela), direita é direita do carro (+x na tela)
        scale_factor = 1.4  # Ajuste para visualização
        for local_x, local_y in local_points:
            # Transformar coordenadas para a visualização:
            # O eixo x da point cloud (frente) mapeia para -y na tela (para cima)
            # O eixo y da point cloud (esquerda) mapeia para -x na tela (para esquerda)
            screen_x = int(center_x - local_y * scale_factor)  # Invertido para corrigir o espelhamento
            screen_y = int(center_y - local_x * scale_factor)  # Frente sempre para cima
            
            if 0 <= screen_x < self.view_width and 0 <= screen_y < self.view_height:
                # Desenhar um pequeno círculo para melhorar a visibilidade
                pygame.draw.circle(local_view, params.red, (screen_x, screen_y), 2)
        
        # Desenhar informação de ângulo atual na tela
        font = pygame.font.SysFont('Arial', 14)
        angle_text = font.render(f"Ângulo: {np.rad2deg(self.car_angle_rad):.2f}°", True, params.white)
        local_view.blit(angle_text, (10, 10))
        
        # Identificar direções cardeais para facilitar a orientação
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
        """Loop principal para manter a janela aberta e executar a simulação."""
        # Criar uma cópia do mapa original para referência de detecção
        self.original_map = self.map.copy()
        
        # Inicializar o carro (apenas com sensores, sem posição)
        self.car = Car(env_map=self.original_map)
        
        running = True

        # Criar uma tela com o triplo da largura para exibir três mapas lado a lado
        width, height = self.map.get_width(), self.map.get_height()
        combined_surface = pygame.display.set_mode((width * 3, height))

        # Inicializar `infomap` como um mapa completamente preto
        self.map.fill(params.black)
        self.infomap = self.map.copy()
        
        # Limpar point cloud no início
        self.global_point_cloud = []

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Capturar teclas pressionadas
            keys = pygame.key.get_pressed()

            # Processar comandos do teclado
            cmd_forward = 0  # -1: trás, 0: parado, 1: frente
            cmd_turn = 0     # -1: direita, 0: reto, 1: esquerda
            
            if keys[pygame.K_w]:
                cmd_forward = 1
            elif keys[pygame.K_s]:
                cmd_forward = -1
                
            if keys[pygame.K_a]:
                cmd_turn = 1  # Esquerda (anti-horário)
            elif keys[pygame.K_d]:
                cmd_turn = -1  # Direita (horário)
            
            # O ambiente move o carro com base nos comandos
            moved = self.move_car(
                cmd_forward=cmd_forward, 
                cmd_turn=cmd_turn,
                map_width=width,
                map_height=height
            )
            
            if moved:
                
                # Atualizar sensores do carro, passando posição e ângulo mantidos pelo ambiente
                sensor_data = self.car.update_sensors(
                    self.original_map, 
                    self.car_position, 
                    self.car_angle_rad
                )
                
                # Armazenar dados em coordenadas globais para visualização
                self.data_storage(sensor_data)
                
                # Atualizar a visualização
                self.show_sensor_data()

            # Criar cópia do mapa original para desenhar o carro
            original_with_car = self.original_map.copy()
            
            # Desenhar o carro
            self.draw_arrow(original_with_car, self.car_position, self.car_angle_rad, size=8, color=params.red)
            
            # Criar visualização local
            local_view = self.create_local_view()

            # **Desenhar o mapa original na esquerda**
            combined_surface.blit(original_with_car, (0, 0))

            # **Desenhar o infomap no meio**
            combined_surface.blit(self.infomap, (width, 0))
            
            # **Desenhar a visualização local à direita**
            combined_surface.blit(local_view, (width * 2, 0))

            # Atualizar a tela
            pygame.display.flip()

            time.sleep(0.01)

        pygame.quit()
    
    def draw_arrow(self, surface, position, angle, size=10, color=params.red):
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