import random 
import numpy as np
# import sys
# np.set_printoptions(threshold=sys.maxsize)
from tile import Tile
import matplotlib.pyplot as plt

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
    def __init__(self, rows, cols, tile_definitions, global_params):
        """
        Initialise la grille.

        rows: int - Nombre de lignes.
        cols: int - Nombre de colonnes.
        tile_definitions: list - Liste des TileDefinition.
        global_params: dict - Paramètres globaux pour les tuiles.
        """
        self.rows = rows
        self.cols = cols
        self.global_params = global_params
        self.grid = [[Tile(tile_definitions) for _ in range(cols)] for _ in range(rows)]

    def simulate_collapse(self):
        """
        Simule le colapso en remplissant la grille avec des tuiles spécifiques.
        """
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid[row][col].collapse()

    def generate_bitmap(self, tile_resolution):
        """
        Gera o bitmap completo da pista com base no grid atual.

        Retorna:
        np.ndarray - Bitmap representando toda a pista.
        """
        tile_size = self.global_params.get('tile_size', 1)
        bitmap = np.zeros((self.rows * tile_resolution, self.cols * tile_resolution))

        # Escala para mapear o grid global para o bitmap
        scale = tile_resolution / tile_size

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
                    resolution=tile_resolution,
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
 
    def plot_bitmap(self, tile_resolution):
        """
        Affiche le bitmap généré pour la piste.
        """
        bitmap = self.generate_bitmap(tile_resolution=tile_resolution)
        plot_debug_grid(self)
        plt.imshow(bitmap, cmap='Greys', origin='lower')
        plt.title("Bitmap de la piste")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.show()