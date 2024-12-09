import json
from tileDefinition import TileDefinition

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

    # Imprimir os resultados
    print(f"Tile Name: {tile_definition.name}")
    print("Parsed Equations:")
    for key, equation in tile_definition.parsed_equations.items():
        print(f"  {key}: {equation}")
    print("Sockets:")
    print(tile_definition.sockets)
    print("-" * 40)