import random

class Tile:
    """
    Représente une instance de tuile avec des possibilités de colapso et une configuration actuelle.
    """

    def __init__(self, tile_definitions):
        """
        Initialise la tuile avec toutes les combinaisons possibles.

        tile_definitions: list - Liste des TileDefinition.
        """
        self.possibilities = [
            {"tile_definition": tile_def, "orientation": orientation,
             "rotated_sockets": self.rotate_sockets(tile_def.sockets, orientation)}
            for tile_def in tile_definitions
            for orientation in range(4)
        ]
        self.collapsed = None  # Aucune tuile sélectionnée au départ

    def rotate_sockets(self,sockets, orientation):
        """
        Tourne les sockets en fonction de l'orientation.

        sockets: dict - Sockets originaux de la tuile (par exemple, {"top": "mid", "bottom": None, ...}).
        orientation: int - Orientation (0: aucune rotation, 1: 90°, 2: 180°, 3: 270°).

        Retourne:
        dict - Sockets tournés.
        """
        ordre_sockets = ["top", "right", "bottom", "left"]
        sockets_tournes = {}
        for i, cote in enumerate(ordre_sockets):
            nouvel_index = (i + orientation) % 4
            sockets_tournes[ordre_sockets[nouvel_index]] = sockets.get(cote)
        return sockets_tournes

    def collapse(self):
        """
        Simule le colapso en choisissant une possibilité aléatoire.
        """
        if self.possibilities:
            self.collapsed = random.choice(self.possibilities)
            # Réduit les possibilités à la sélectionnée
            self.possibilities = [self.collapsed]
