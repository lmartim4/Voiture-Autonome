class WaveFunctionCollapse:
    def __init__(self, grid, tile_definitions):
        """
        Initializes WFC on a given grid with tile definitions.

        grid: Grid - Instance of the Grid class containing tiles and possibilities.
        tile_definitions: list - List of TileDefinition defining the rules.
        """
        self.grid = grid
        self.tile_definitions = tile_definitions

    def is_valid_socket_match(self, socket_a, socket_b):
        """
        Checks if two sockets are compatible.

        socket_a: str or None - Socket of the first tile.
        socket_b: str or None - Socket of the second tile.

        Returns:
        bool - True if the sockets are compatible, otherwise False.
        """
        return socket_a == socket_b

    def apply_boundary_conditions(self):
        """
        Applies boundary conditions to the edges of the grid.
        All sockets pointing outward must be null.
        """
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                tile = self.grid.grid[row][col]
                if row == 0:  # Top border
                    tile.possibilities = [
                        p for p in tile.possibilities if p["rotated_sockets"]["top"] is None
                    ]
                if row == self.grid.rows - 1:  # Bottom border
                    tile.possibilities = [
                        p for p in tile.possibilities if p["rotated_sockets"]["bottom"] is None
                    ]
                if col == 0:  # Left border
                    tile.possibilities = [
                        p for p in tile.possibilities if p["rotated_sockets"]["left"] is None
                    ]
                if col == self.grid.cols - 1:  # Right border
                    tile.possibilities = [
                        p for p in tile.possibilities if p["rotated_sockets"]["right"] is None
                    ]

                self.propagate_constraints(row, col)

    def propagate_constraints(self, row, col):
        """
        Propagates connectivity constraints from a given cell.

        row: int - Row index of the current cell.
        col: int - Column index of the current cell.
        """

        # Order:
        # Neighbor's row, col
        # Neighbor socket, corresponding socket
        neighbors = [
            (row + 1, col, "bottom", "top"),  # Cell below
            (row - 1, col, "top", "bottom"),  # Cell above
            (row, col - 1, "left", "right"),  # Cell to the left
            (row, col + 1, "right", "left"),  # Cell to the right
        ]

        for neighbor_row, neighbor_col, our_socket, their_socket in neighbors:
            if 0 <= neighbor_row < self.grid.rows and 0 <= neighbor_col < self.grid.cols:
                current_tile = self.grid.grid[row][col]
                neighbor_tile = self.grid.grid[neighbor_row][neighbor_col]

                # Collect all possibilities that are compatible with the neighbor
                valid_possibilities = []
                for possibility in neighbor_tile.possibilities:
                    if any(
                        self.is_valid_socket_match(
                            possibility["rotated_sockets"][their_socket],
                            p["rotated_sockets"][our_socket]
                        ) for p in current_tile.possibilities
                    ):
                        valid_possibilities.append(possibility)

                neighbor_tile.possibilities = valid_possibilities

    def step_callback(self, step, row, col):
        print("="*100,"\n")
        print(f"Now, at step {step}, we collapsed cell ({col}, {row}) to ", self.grid.grid[row][col].possibilities[0]["tile_definition"].name, " at ", self.grid.grid[row][col].possibilities[0]["orientation"] * 90," degrees\n")
        print("="*100)
        self.grid.plot_debug_grid()
        self.grid.draw_bitmap()
        self.grid.plot_bitmap(debug=True)  # Show the state after each step

    def collapse(self, debug=False):
        """
        Executes the WFC algorithm to resolve the entire grid.

        step_callback: function - Optional callback for each step, receiving
        (step, row, col, grid) as arguments.
        """
        self.apply_boundary_conditions()

        step = 0

        while True:
            # Find the non-collapsed cell with the fewest possibilities
            min_possibilities = float("inf")
            next_cell = None

            for row in range(self.grid.rows):
                for col in range(self.grid.cols):
                    tile = self.grid.grid[row][col]
                    if tile.collapsed is None and 1 <= len(tile.possibilities) < min_possibilities:
                        min_possibilities = len(tile.possibilities)
                        next_cell = (row, col)

            # If no cell is found to collapse, the process is complete
            if next_cell is None:
                break

            # Collapse the cell with the fewest possibilities
            row, col = next_cell
            self.grid.grid[row][col].collapse()

            # Debug callback
            if debug:
                self.step_callback(step, row, col)

            # Propagate constraints from this cell
            self.propagate_constraints(row, col)
            step += 1

        # Final check: all cells should be collapsed
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                if self.grid.grid[row][col].collapsed is None:
                    raise RuntimeError("Unable to resolve the grid. Some cells remain uncertain.")

        print("Grid successfully resolved!")
