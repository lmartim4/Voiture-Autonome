import json
import numpy as np
import matplotlib.pyplot as plt
from generateurDePiste import construire_grille

# Exemple d'utilisation
if __name__ == "__main__":
    grid = construire_grille(config_path='tile_config.json', rows=5, cols=5, tile_resolution=100) 

    # Afficher le bitmap de la piste
    grid.plot_bitmap(tile_resolution=100)