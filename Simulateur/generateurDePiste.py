import random

class WaveFunctionCollapse:
    def __init__(self, grid, tile_definitions):
        """
        Initialise le WFC sur une grille donnée avec des définitions de tuiles.

        grid: Grid - Instance de la classe Grid contenant les tuiles et les possibilités.
        tile_definitions: list - Liste des TileDefinition définissant les règles.
        """
        self.grid = grid
        self.tile_definitions = tile_definitions

    def is_valid_socket_match(self, socket_a, socket_b):
        """
        Vérifie si deux sockets sont compatibles.

        socket_a: str ou None - Socket de la première tuile.
        socket_b: str ou None - Socket de la deuxième tuile.

        Retourne:
        bool - True si les sockets sont compatibles, sinon False.
        """
        return socket_a == socket_b

    def apply_boundary_conditions(self):
        """
        Applique les conditions de contournement pour les bords de la grille.
        Toutes les sockets qui pointent vers l'extérieur doivent être nulles.
        """
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                tile = self.grid.grid[row][col]
                if row == 0:  # Bord superieur 
                    tile.possibilities = [
                        p for p in tile.possibilities if p["rotated_sockets"]["top"] is None
                    ]
                if row == self.grid.rows - 1:  # Bord inferieur 
                    tile.possibilities = [
                        p for p in tile.possibilities if p["rotated_sockets"]["bottom"] is None
                    ]
                if col == 0:  # Bord gauche
                    tile.possibilities = [
                        p for p in tile.possibilities if p["rotated_sockets"]["left"] is None
                    ]
                if col == self.grid.cols - 1:  # Bord droit
                    tile.possibilities = [
                        p for p in tile.possibilities if p["rotated_sockets"]["right"] is None
                    ]


                self.propagate_constraints(row, col)        
                # print(f"Para a tile {row},{col} temos as possibilidades :\n")
                # for possibility in tile.possibilities:
                #     print(possibility["tile_definition"].name, possibility["orientation"] * 90)


    def propagate_constraints(self, row, col):
        """
        Propage les contraintes de connectivité à partir d'une cellule donnée.

        row: int - Ligne de la cellule actuelle.
        col: int - Colonne de la cellule actuelle.
        """
        
        # Order : 
        # neighbour's row, col
        # Neighbour socket, your (matching) socket
        neighbors = [
            (row + 1, col, "bottom", "top"),  # Cellule en-dessous
            (row - 1, col, "top", "bottom"),  # Cellule au-dessus
            (row, col - 1, "left", "right"),  # Cellule à gauche
            (row, col + 1, "right", "left"),  # Cellule à droite
        ]

        for neighbor_row, neighbor_col, our_socket, their_socket in neighbors:
            if 0 <= neighbor_row < self.grid.rows and 0 <= neighbor_col < self.grid.cols:
                current_tile = self.grid.grid[row][col]
                neighbor_tile = self.grid.grid[neighbor_row][neighbor_col]

                # Collecte toutes les possibilités compatibles avec le voisin
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

    def collapse(self, step_callback=None):
        """
        Executa o WFC para resolver a grade inteira.

        step_callback: function - Callback opcional para cada passo, recebendo
        (passo, linha, coluna, grid) como argumentos.
        """
        self.apply_boundary_conditions()

        step = 0

        while True:
            # Encontrar a célula não colapsada com o menor número de possibilidades
            min_possibilities = float("inf")
            next_cell = None

            for row in range(self.grid.rows):
                for col in range(self.grid.cols):
                    tile = self.grid.grid[row][col]
                    if tile.collapsed is None and 1 <= len(tile.possibilities) < min_possibilities:
                        min_possibilities = len(tile.possibilities)
                        next_cell = (row, col)

            # Se nenhuma célula a colapsar for encontrada, o processo está concluído
            if next_cell is None:
                break

            # Colapsar a célula com o menor número de possibilidades
            row, col = next_cell
            print("Originalmente estavamos em ", self.grid.grid[row][col].possibilities, " em (", col, ", ", row, ") ---------------- \n" )
            self.grid.grid[row][col].collapse()

            # Callback para debug
            if step_callback:
                step_callback(step, row, col, self.grid)

            # Propagar as restrições a partir dessa célula
            self.propagate_constraints(row, col)
            step += 1

        # Verificação final: todas as células devem estar colapsadas
        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                if self.grid.grid[row][col].collapsed is None:
                    raise RuntimeError("Impossível resolver a grade. Algumas células permanecem incertas.")

        print("Grille résolue avec succès !")
