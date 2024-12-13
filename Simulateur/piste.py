import random 
import numpy as np
from tile import Tile
import matplotlib.pyplot as plt

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
        Génère un bitmap complet de la piste à partir de la grille actuelle.

        Retourne:
        np.ndarray - Bitmap représentant la piste entière.
        """
        tile_size = self.global_params.get('tile_size', 1)
        bitmap = np.zeros((self.rows * tile_resolution, self.cols * tile_resolution))

        scale = tile_resolution / tile_size

        for row in range(self.rows):
            for col in range(self.cols):
                tile = self.grid[row][col].collapsed
                if tile is None:
                    continue

                local_bitmap = tile["tile_definition"].generate_bitmap(
                    global_params=self.global_params,
                    resolution=tile_resolution,
                    grid_size=int(tile_size * scale),
                    orientation=tile["orientation"]
                )

                offset_x = int(col * tile_size * scale)
                offset_y = int(row * tile_size * scale)

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
        plt.imshow(bitmap, cmap='Greys', origin='lower')
        plt.title("Bitmap de la piste")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.show()