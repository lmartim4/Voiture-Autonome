import json
import matplotlib.pyplot as plt
from tileDefinition import TileDefinition
from track import Grid
from waveFunctionCollapse import WaveFunctionCollapse
import numpy as np

def generate_and_display_track():
    """
    Generates a track using WFC and displays it, allowing the user to save or generate a new one.
    """
    # Load the JSON configuration file
    with open('configs/tile_config.json', 'r') as file:
        data = json.load(file)

    # Extract global parameters and tiles
    debug = data["debug"]
    global_params = data["global_params"]
    tiles = data["tiles"]

    # Create tile definitions
    tile_definitions = [TileDefinition.from_config(tile, global_params) for tile in tiles]

    track_number = 0
    while True:  # Loop until the user closes the window
        # Initialize the grid
        grid = Grid(tile_definitions=tile_definitions, global_params=global_params)

        # Instantiate WFC
        wfc = WaveFunctionCollapse(grid, tile_definitions)

        # Execute WFC
        try:
            wfc.collapse(debug=data["debug"])
        except RuntimeError as e:
            print(f"Error while solving the grid: {e}")
            print("Current grid state:")
            grid.plot_bitmap()
            continue  # Retry on failure

        # Generate the bitmap
        grid.track_number = track_number
        grid.generate_bitmap()
        grid.plot_bitmap(debug=debug)
        track_number = grid.track_number

        if track_number is None:
            break

if __name__ == "__main__":
    generate_and_display_track()
