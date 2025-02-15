import numpy as np
import cv2

from tile import Tile

import matplotlib
matplotlib.use("GTK3Agg")
import matplotlib.pyplot as plt

def plot_debug_grid(grid):
    """
    Visualiza o estado atual da grade com informações de debug.

    grid: Grid - Instância da classe Grid contendo o estado atual da pista.
    """
    rows, cols = grid.rows, grid.cols
    fig, ax = plt.subplots(figsize=(cols * 1.5, rows * 1.5))  # Ajuste do tamanho do gráfico

    # Configurar limites da grade
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.invert_yaxis()  # Para alinhar o eixo (0, 0) no canto inferior esquerdo

    # Desenhar linhas da grade
    for x in range(cols + 1):
        ax.axvline(x, color='black', linewidth=0.5)
    for y in range(rows + 1):
        ax.axhline(y, color='black', linewidth=0.5)

    # Preencher informações em cada célula
    for row in range(rows):
        for col in range(cols):
            tile = grid.grid[row][col]
            if tile is None or not tile.collapsed:
                # Célula não colapsada
                text = "?"
            else:
                # Tile colapsada
                definition = tile.collapsed["tile_definition"].name
                orientation = tile.collapsed["orientation"] * 90
                text = f"{definition}\n{orientation}°"

            # Adicionar texto ao centro da célula
            ax.text(
                col + 0.5, row + 0.5, text,
                fontsize=8, ha='center', va='center',
                bbox=dict(boxstyle="round", facecolor="white", edgecolor="black", alpha=0.7)
            )

    # Configurar o gráfico
    ax.set_xticks(range(cols))
    ax.set_yticks(range(rows))
    ax.set_xticklabels(range(cols))
    ax.set_yticklabels(range(rows))
    ax.set_aspect('equal')
    ax.grid(False)

    plt.tight_layout()  # Ajustar o layout automaticamente
    plt.title("Estado Atual da Grid")
    plt.show()

class Grid:
    """
    Représente la grille contenant des instances de Tile.
    """
    def __init__(self, tile_definitions, global_params):
        """
        Initialise la grille.

        tile_definitions: list - Liste des TileDefinition.
        global_params: dict - Paramètres globaux pour les tuiles.
        """
        self.rows = global_params["n_rows"]
        self.cols = global_params["n_cols"]
        self.tile_resolution = global_params["tile_resolution"]
        self.global_params = global_params
        self.grid = [[Tile(tile_definitions) for _ in range(self.cols)] for _ in range(self.rows)]

    def simulate_collapse(self):
        """
        Simule le colapso en remplissant la grille avec des tuiles spécifiques.
        """
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid[row][col].collapse()

    def generate_bitmap(self):
        """
        Gera o bitmap completo da pista com base no grid atual.

        Retorna:
        np.ndarray - Bitmap representando toda a pista.
        """
        tile_size = self.global_params.get('tile_size', 1)
        bitmap = np.zeros((self.rows * self.tile_resolution, self.cols * self.tile_resolution))

        # Escala para mapear o grid global para o bitmap
        scale = self.tile_resolution / tile_size

        for row in range(self.rows):
            for col in range(self.cols):
                tile_data = self.grid[row][col]
                if tile_data is None or not tile_data.collapsed:
                    continue

                tile = tile_data.collapsed["tile_definition"]
                orientation = tile_data.collapsed["orientation"]

                # Gerar bitmap para a tile específica
                local_bitmap = tile.generate_bitmap(
                    global_params=self.global_params,
                    grid_size=int(tile_size * scale),
                    orientation=orientation
                )

                # Calcular o deslocamento no grid
                offset_x = int(col * tile_size * scale)
                offset_y = int((self.rows - 1 - row) * tile_size * scale)  # Inverte a ordem das linhas

                # Inserir o bitmap local no bitmap global
                for i in range(local_bitmap.shape[0]):
                    for j in range(local_bitmap.shape[1]):
                        if local_bitmap[i, j] > 0:
                            bitmap[offset_y + i, offset_x + j] = 1

        return bitmap
    
    def dilate_track(self,bitmap):
        """
        Aplica uma dilatação no bitmap da pista para "engordar" as linhas.

        bitmap: np.ndarray - Matriz representando a pista (0 = fundo, 1 = pista).
        kernel_size: int - Tamanho do kernel para a dilatação.
        iterations: int - Número de iterações da dilatação.

        Retorna:
        np.ndarray - Bitmap dilatado.
        """
        
        kernel_size = self.global_params["dilation_kernel_size"]
        iterations = self.global_params["dilation_iter"]

        # Converter o bitmap para formato binário (0 e 255)
        binary_image = (bitmap * 255).astype(np.uint8)

        # Criar um kernel (elemento estruturante) para a dilatação
        kernel = np.ones((kernel_size, kernel_size), np.uint8)

        # Aplicar a dilatação
        dilated_image = cv2.dilate(binary_image, kernel, iterations=iterations)

        return dilated_image

 
    def plot_bitmap(self):
        """
        Affiche le bitmap généré pour la piste.
        """
        bitmap = self.generate_bitmap()
        bitmap = self.dilate_track(bitmap)
        plt.imshow(bitmap, cmap='Greys', origin='lower')
        plt.title("Bitmap de la piste")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.show()

        # plot_debug_grid(self)
