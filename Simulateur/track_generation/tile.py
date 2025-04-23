import random

class Tile:
    """
    Represents a tile instance with collapse possibilities and a current configuration.
    """

    def __init__(self, tile_definitions):
        """
        Initializes the tile with all possible combinations.

        tile_definitions: list - List of TileDefinition.
        """
        self.possibilities = [
            {"tile_definition": tile_def, "orientation": orientation,
             "rotated_sockets": self.rotate_sockets(tile_def.sockets, orientation)}
            for tile_def in tile_definitions
            for orientation in range(4)
        ]

        # Remove redundant "empty" tile rotations
        self.possibilities = [p for p in self.possibilities if not (p["tile_definition"].name == "empty" and p["orientation"] > 0)]
        
        # Remove redundant "straight" tile rotations
        self.possibilities = [p for p in self.possibilities if not (p["tile_definition"].name == "straight" and p["orientation"] in [2,3])]

        # for possibility in self.possibilities:
        #     print(possibility["tile_definition"].name, possibility["orientation"] * 90)        
        
        # print("="*50)
        
        # print(self.possibilities)
        self.collapsed = None  # No tile selected initially

    def rotate_sockets(self, sockets, orientation):
        """
        Rotates the sockets based on the orientation.

        sockets: dict - Original sockets of the tile (e.g., {"top": "mid", "bottom": None, ...}).
        orientation: int - Orientation (0: no rotation, 1: 90°, 2: 180°, 3: 270°).

        Returns:
        dict - Rotated sockets.
        """
        socket_order = ["top", "right", "bottom", "left"]
        rotated_sockets = {}
        for i, side in enumerate(socket_order):
            new_index = (i + orientation) % 4
            rotated_sockets[socket_order[new_index]] = sockets.get(side)
        return rotated_sockets

    def collapse(self):
        """
        Simulates the collapse process by selecting a random possibility.
        """
        if self.possibilities:
            self.collapsed = random.choice(self.possibilities)
            # Reduce possibilities to the selected one
            self.possibilities = [self.collapsed]

