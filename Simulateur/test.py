import json
import numpy as np
import matplotlib.pyplot as plt
from tileDefinition import TileDefinition

# Flag para decidir se deve printar os arrays
PRINT_POINTS = False

def generate_bitmap(tile, global_params, resolution=500, grid_size=100, orientation=0):
    """
    Gera um bitmap para uma única tile.

    tile: TileDefinition - Instância da tile.
    global_params: dict - Parâmetros globais, incluindo tile_size.
    resolution: int - Resolução para cada tile.
    grid_size: int - Tamanho da matriz do bitmap.
    orientation: int - Orientação da tile (0, 1, 2, 3).

    Retorna:
    np.ndarray - Bitmap da tile.
    """
    tile_size = global_params.get('tile_size', 1)
    bitmap = np.zeros((grid_size, grid_size))  # Inicializar o bitmap vazio

    # Escala para mapear o espaço contínuo para o grid discreto
    scale = grid_size / tile_size

    # Gerar pontos para a orientação especificada
    points = tile.evaluate(orientation=orientation, resolution=resolution, global_params=global_params)

    # Mapear pontos para o bitmap
    for side, pts in points.items():
        # print(pts)
        for x, y in pts:
            # Converter coordenadas contínuas para índices no bitmap
            i = int(y * scale)  # Índice da linha
            j = int(x * scale)  # Índice da coluna
            # print(i,j)
            if 0 <= i < grid_size and 0 <= j < grid_size:
                # print("Setei (", i,", ",j, ")")
                bitmap[i, j] = 1  # Marca o pixel como parte da pista

    return bitmap

def inspectTile(tile_name, resolution, thickness, orientation, tile_definitions, global_params):
    """
    Inspeciona uma tile específica e gera seu bitmap.

    tile_name: str - Nome da tile a ser inspecionada.
    resolution: int - Resolução para cada tile.
    thickness: int - Espessura da pista no bitmap.
    orientation: int - Orientação da tile (0, 1, 2, 3).
    tile_definitions: list - Lista de instâncias TileDefinition.
    global_params: dict - Parâmetros globais, incluindo tile_size.

    Retorna:
    None
    """
    # Encontrar a tile pelo nome
    tile = next((t for t in tile_definitions if t.name == tile_name), None)
    if tile is None:
        print(f"Tile '{tile_name}' não encontrada.")
        return

    print(f"Inspecionando Tile: {tile_name}")
    print(f"Orientação: {orientation * 90}°")
    print(f"Resolução: {resolution}")
    print(f"Espessura: {thickness}")

    # Gerar o bitmap
    grid_size = 200  # Tamanho fixo para o bitmap
    bitmap = generate_bitmap(tile, global_params, resolution=resolution, grid_size=grid_size, orientation=orientation)

    # Printar os pontos se a flag estiver ativa
    if PRINT_POINTS:
        points = tile.evaluate(orientation=orientation, resolution=resolution, global_params=global_params)
        for side, pts in points.items():
            print(f"  {side}: {pts}")

    # Plotar o bitmap
    plt.imshow(bitmap, cmap='Greys', origin='lower')
    plt.title(f"Bitmap da Tile: {tile_name} | Orientação: {orientation * 90}°")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.show()


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

for tile in tile_definitions:
    
    for orientation in range(4):
        # Inspecionar uma tile específica
        inspectTile(
            tile_name=tile.name,        # Nome da tile a inspecionar
            resolution=500,            # Resolução para gerar os pontos
            thickness=1,               # Espessura no bitmap
            orientation=orientation,             # Orientação (0, 1, 2, 3)
            tile_definitions=tile_definitions,
            global_params=global_params
        )