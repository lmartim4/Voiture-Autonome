import json
import matplotlib.pyplot as plt
from tileDefinition import TileDefinition
from importlib import reload
import tileDefinition
reload(tileDefinition)

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
    print("Domains")
    print(tile_definition)
    print("Sockets:")
    print(tile_definition.sockets)

    # Testar avaliação das equações para resolução padrão
    print("\nSample points from equations:")

    for orientation in range(4):

        points = tile_definition.evaluate(resolution=500, orientation=orientation, global_params = global_params)  # Teste com poucos pontos
        # Plotar as bordas da tile
        plt.figure(figsize=(5, 5))
        for side, pts in points.items():
            plt.plot(pts[:, 0], pts[:, 1], label=side)

        plt.title(f"Tile: {tile_definition.name} | Orientation: {orientation * 90}°")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.legend()
        plt.axis("equal")
        plt.grid(True)
        plt.show()

        # for side, pts in points.items():
            # print(f"  {side}: {pts}")
        # print("-" * 40)
