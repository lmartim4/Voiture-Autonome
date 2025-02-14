import json
from tileDefinition import TileDefinition
from piste import Grid
from generateurDePiste import WaveFunctionCollapse

import os
os.environ["PYTHONWARNINGS"] = "ignore"

def test_wave_function_collapse():
    """
    Teste básico para a implementação do Wave Function Collapse (WFC).
    """
    # Carregar o arquivo JSON de configuração
    with open('tile_config.json', 'r') as file:
        data = json.load(file)

    # Extrair parâmetros globais e tiles
    global_params = data["global_params"]
    tiles = data["tiles"]

    # Criar definições de tiles
    tile_definitions = [TileDefinition.from_config(tile, global_params) for tile in tiles]

    # Inicializar a grade (grid)
    rows, cols = 5, 5  # Tamanho da grade
    grid = Grid(rows=rows, cols=cols, tile_definitions=tile_definitions, global_params=global_params)

    # Instanciar o WFC
    wfc = WaveFunctionCollapse(grid, tile_definitions)

    # Executar o WFC
    try:
        def step_callback(step, row, col, grid):
            print(f"Agora, no passo {step}, colapsamos a célula ({col}, {row}) para ", grid.grid[row][col].possibilities, " ---------------- \n")
            grid.plot_bitmap(tile_resolution=50)  # Mostrar estado após cada passo

        wfc.collapse(step_callback=None)
    except RuntimeError as e:
        print(f"Erro ao resolver a grade: {e}")
        print("Estado atual da grade:")
        grid.plot_bitmap(tile_resolution=100)  # Mostrar o estado atual da grade mesmo em caso de erro
        return

    # Gerar e plotar o bitmap da pista resolvida
    grid.plot_bitmap(tile_resolution=100)

    # Verificar se todas as tiles estão colapsadas
    for row in grid.grid:
        for tile in row:
            assert tile.collapsed is not None, "Alguma tile não foi colapsada corretamente!"

    print("Teste concluído com sucesso! A grade foi resolvida.")

if __name__ == "__main__":
    test_wave_function_collapse()
