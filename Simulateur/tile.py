
class Tile:
    def __init__(self, x, y, allowed_tiles):
        """
        x, y: int - Posição da tile na grid.
        allowed_tiles: list - Lista de tiles possíveis (nome + orientação).
                             Ex: [('straight', 0), ('curved', 1)].
        """
        self.x = x
        self.y = y
        self.allowed_tiles = allowed_tiles  # Lista de possibilidades (nome + orientação)
        self.collapsed_tile = None         # Armazena a tile final (se colapsada)

    def collapse(self, chosen_tile):
        """
        Colapsa a célula para uma única tile e remove outras opções.
        chosen_tile: tuple - (nome da tile, orientação).
        """
        self.allowed_tiles = [chosen_tile]
        self.collapsed_tile = chosen_tile

    def restrict(self, constraints):
        """
        Aplica restrições às tiles permitidas.
        constraints: list - Lista de tiles válidas com base nas regras de conectividade.
        
        Remove as tiles que não atendem às restrições.
        """
        self.allowed_tiles = [
            tile for tile in self.allowed_tiles
            if tile in constraints
        ]

    def is_collapsed(self):
        """Retorna True se a tile já foi colapsada."""
        return len(self.allowed_tiles) == 1
