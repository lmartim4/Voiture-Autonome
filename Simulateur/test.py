import json
import numpy as np
import matplotlib.pyplot as plt
from tileDefinition import TileDefinition
# from debugUtils import *
from piste import Grid

# Carregar o arquivo JSON
with open('tile_config.json', 'r') as file:
    data = json.load(file)

# Extrair parâmetros globais e lista de tiles
global_params = data["global_params"]
tiles = data["tiles"]

# Processar cada tile da lista
tile_definitions = []
for tile_config in tiles:
    tile_definition = TileDefinition.from_config(tile_config, global_params)
    tile_definitions.append(tile_definition)

# Testar o Grid e Simulação de Colapso
if __name__ == "__main__":
    import json

    # Carregar o arquivo JSON
    with open('tile_config.json', 'r') as file:
        data = json.load(file)

    # Extrair parâmetros globais e lista de tiles
    global_params = data["global_params"]
    tiles = data["tiles"]

    # Criar instâncias TileDefinition
    tile_definitions = [TileDefinition.from_config(tile, global_params) for tile in tiles]

    # Inicializar o Grid
    grid = Grid(rows=5, cols=5, tile_definitions=tile_definitions, global_params=global_params)

    # Simular colapso aleatório
    grid.simulate_collapse()

    # Plotar o bitmap da pista
    grid.plot_bitmap(tile_resolution = 100)
