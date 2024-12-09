import json

# Carregar configurações do arquivo
with open('config.json', 'r') as f:
    config = json.load(f)

global_params = config['global_params']
tile_definitions = [
    TileDefinition.from_config(tile_config, global_params)
    for tile_config in config['tiles']
]

# Dicionário para acessar as definições por nome
tile_library = {tile.name: tile for tile in tile_definitions}
