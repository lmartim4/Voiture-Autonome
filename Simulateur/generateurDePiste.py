import json
from tileDefinition import TileDefinition
from piste import Grid

# Fonction pour construire une grille

def construire_grille(config_path, rows, cols, tile_resolution):
    """
    Charge la configuration et construit une grille.

    config_path: str - Chemin du fichier JSON de configuration.
    rows: int - Nombre de lignes dans la grille.
    cols: int - Nombre de colonnes dans la grille.
    tile_resolution: int - Résolution des tuiles pour le bitmap.

    Retourne:
    Grid - Instance de la grille générée.
    """
    with open(config_path, 'r') as file:
        data = json.load(file)

    global_params = data["global_params"]
    tiles = data["tiles"]

    tile_definitions = [TileDefinition.from_config(tile, global_params) for tile in tiles]

    grid = Grid(rows=rows, cols=cols, tile_definitions=tile_definitions, global_params=global_params)
    grid.simulate_collapse()

    return grid