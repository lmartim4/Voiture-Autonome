import random 
import numpy as np
import matplotlib.pyplot as plt

def rotate_sockets(sockets, orientation):
    """
    Rotaciona os sockets de acordo com a orientação.

    sockets: dict - Sockets originais da tile (e.g., {"top": "mid", "bottom": None, ...}).
    orientation: int - Orientação (0: sem rotação, 1: 90°, 2: 180°, 3: 270°).

    Retorna:
    dict - Sockets rotacionados.
    """
    # Ordem dos sockets no sentido horário
    socket_order = ["top", "right", "bottom", "left"]
    
    # Criação da nova configuração após a rotação
    rotated_sockets = {}
    for i, side in enumerate(socket_order):
        # Determinar o novo índice após a rotação
        new_index = (i + orientation) % 4
        rotated_sockets[socket_order[new_index]] = sockets.get(side)

    return rotated_sockets

class Grid:
    def __init__(self, rows, cols, tile_definitions, global_params):
        """
        Inicializa a grade para a pista.
        
        rows: int - Número de linhas no grid.
        cols: int - Número de colunas no grid.
        tile_definitions: list - Lista de instâncias TileDefinition.
        global_params: dict - Parâmetros globais para tiles.
        """
        self.rows = rows
        self.cols = cols
        self.global_params = global_params
        
        # Todas as combinações possíveis de tiles (TileDefinition x Orientações)
        self.tiles = [
            {"tile": tile,
             "orientation": orientation,
            "rotated_sockets": rotate_sockets(tile.sockets, orientation)  # Inclui sockets rotacionados 
            }
            for tile in tile_definitions
            for orientation in range(4)
        ]

        # Inicializar a pista como um grid vazio (None em cada célula)
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]

    def simulate_collapse(self):
        """
        Preenche o grid aleatoriamente com tiles, simulando um colapso aleatório.
        """
        for row in range(self.rows):
            for col in range(self.cols):
                # Escolher uma combinação aleatória de tile + orientação
                chosen_tile = random.choice(self.tiles)
                self.grid[row][col] = chosen_tile

                # Debug: Mostrar os sockets rotacionados
                print(f"Tile at ({row}, {col}): {chosen_tile['tile'].name}")
                print(f"Orientation: {chosen_tile['orientation'] * 90}°")
                print(f"Sockets: {chosen_tile['rotated_sockets']}")


    def generate_bitmap(self, tile_resolution):
        """
        Gera o bitmap completo da pista com base no grid atual.
        
        Retorna:
        np.ndarray - Bitmap representando toda a pista.
        """
        tile_size = self.global_params.get('tile_size', 1)
        bitmap = np.zeros((self.rows *tile_resolution, self.cols * tile_resolution))

        # Escala para mapear o grid global para o bitmap
        scale = tile_resolution / tile_size 

        for row in range(self.rows):
            for col in range(self.cols):
                tile_data = self.grid[row][col]
                if tile_data is None:
                    continue

                tile = tile_data["tile"]
                orientation = tile_data["orientation"]

                # Gerar bitmap para a tile específica
                local_bitmap = tile.generate_bitmap(
                    global_params=self.global_params,
                    resolution=tile_resolution,
                    grid_size=int(tile_size * scale),
                    orientation=orientation
                )

                # Calcular o deslocamento no grid
                offset_x = int(col * tile_size * scale)
                offset_y = int(row * tile_size * scale)

                # Inserir o bitmap local no bitmap global
                for i in range(local_bitmap.shape[0]):
                    for j in range(local_bitmap.shape[1]): 
                        # print(i,j)
                        if local_bitmap[i, j] > 0:
                            bitmap[offset_y + i, offset_x + j] = 1
        # print(bitmap)

        return bitmap

    def plot_bitmap(self, tile_resolution):
        """
        Plota o bitmap da pista gerada.
        """
        bitmap = self.generate_bitmap(tile_resolution=tile_resolution)
        plt.imshow(bitmap, cmap='Greys', origin='lower')
        plt.title("Bitmap da Pista")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.show()