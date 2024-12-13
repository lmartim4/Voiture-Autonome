import numpy as np
import matplotlib.pyplot as plt

# Flag para decidir se deve printar os arrays
PRINT_POINTS = False

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

