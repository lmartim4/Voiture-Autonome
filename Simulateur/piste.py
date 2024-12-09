
class Grid:
    def __init__(self, size, tile_types):
        """
        size: int - Tamanho da grade (size x size).
        tile_types: list - Lista de todos os tipos possíveis de tiles.
        """
        self.size = size
        self.grid = [[list(tile_types) for _ in range(size)] for _ in range(size)]

    def get_tile(self, x, y):
        """Retorna o tile na posição (x, y)."""
        if 0 <= x < self.size and 0 <= y < self.size:
            return self.grid[y][x]
        return None

    def collapse_tile(self, x, y, tile):
        """Colapsa uma célula para um tile específico."""
        self.grid[y][x] = [tile]

    def is_collapsed(self):
        """Verifica se toda a grade está colapsada."""
        for row in self.grid:
            for cell in row:
                if len(cell) > 1:  # Mais de um tile possível
                    return False
        return True

    def get_least_entropy_cell(self):
        """Retorna a posição da célula com menor número de opções (entropia)."""
        min_entropy = float('inf')
        target = None
        for y in range(self.size):
            for x in range(self.size):
                if len(self.grid[y][x]) > 1 and len(self.grid[y][x]) < min_entropy:
                    min_entropy = len(self.grid[y][x])
                    target = (x, y)
        return target
