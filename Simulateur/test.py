import json
from tileDefinition import TileDefinition
from track import Grid
from trackGenerator import WaveFunctionCollapse

def test_wave_function_collapse():
    """
    Basic test for the implementation of Wave Function Collapse (WFC).
    """
    # Load the JSON configuration file
    with open('configs/extended_tile_config.json', 'r') as file:
        data = json.load(file)

    # Extract global parameters and tiles
    debug = data["debug"]
    global_params = data["global_params"]
    tiles = data["tiles"]

    # Create tile definitions
    tile_definitions = [TileDefinition.from_config(tile, global_params) for tile in tiles]

    # Initialize the grid
    grid = Grid(tile_definitions=tile_definitions, global_params=global_params)

    # Instantiate WFC
    wfc = WaveFunctionCollapse(grid, tile_definitions)

    # Execute WFC
    try:
        wfc.collapse(debug=debug)
    except RuntimeError as e:
        print(f"Error while solving the grid: {e}")
        print("Current grid state:")
        grid.plot_bitmap()  # Show the current grid state even in case of an error
        return

    grid.generate_bitmap()
    # Generate and plot the final track bitmap
    grid.plot_bitmap()
    # grid.plot_bitmap(block=False)
    # grid.plot_debug_grid()

if __name__ == "__main__":
    test_wave_function_collapse()

