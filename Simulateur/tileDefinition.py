import numpy as np
from sympy import symbols, sympify

class TileDefinition:
    def __init__(self, name, equations, sockets):
        """
        name: str - Nome da tile (e.g., 'straight', 'curved').
        equations: dict - Equações que definem a geometria da pista.
                          Ex: {'top': 'y = 0.75', 'bottom': 'y = 0.25'}.
        sockets: dict - Definições de conectividade com base nas orientações.
                        Ex: {'top': 'in', 'bottom': 'out', 'left': None, 'right': None}.
        """
        self.name = name
        self.equations = equations  # Raw equations as strings
        self.sockets = sockets      # Connectivity rules (e.g., 'in', 'out', None)
        self.parsed_equations = self.parse_equations(equations)  # Parsed equations (as functions)

    def parse_equations(self, equations):
        """
        Converte as equações definidas em strings para funções utilizáveis.
        """
        parsed = {}
        x = symbols('x')
        for key, eq in equations.items():
            parsed[key] = sympify(eq)  # Converte para expressão simbólica
        return parsed

    @classmethod
    def from_config(cls, config, global_params):
        """
        Cria uma TileDefinition a partir de uma configuração (uma única tile do arquivo JSON).

        config: dict - Configuração da tile (um item da lista 'tiles').
        global_params: dict - Parâmetros globais (e.g., largura da pista).
        """
        # Substituir parâmetros globais nas equações
        equations = {
            key: eq.replace("tile_size", str(global_params['tile_size']))
                   .replace("track_width", str(global_params['track_width']))
            for key, eq in config['equations'].items()
        }
        
        return cls(config['name'], equations, config['sockets'])


    # def evaluate(self, orientation, resolution=100):
    #     """
    #     Gera os pontos (numpy arrays) da geometria da pista baseada nas equações.
    #     orientation: int - Orientação da tile (0, 1, 2, 3).
    #     resolution: int - Número de pontos gerados para as curvas.
        
    #     Retorna:
    #     dict - Contém arrays numpy de pontos para cada borda.
    #            Ex: {'top': np.array([[x1, y1], [x2, y2], ...]), ...}
    #     """
    #     points = {}
    #     x_vals = np.linspace(-0.5, 0.5, resolution)  # Coordenadas globais do tile (1x1 grid)

    #     for side, eq in self.parsed_equations.items():
    #         y_vals = [float(eq.evalf(subs={'x': x})) for x in x_vals]  # Avalia a equação
    #         points[side] = np.column_stack((x_vals, y_vals))

    #     # Rotaciona os pontos de acordo com a orientação
    #     if orientation:
    #         points = self.rotate_points(points, orientation)

    #     return points

    # def rotate_points(self, points, orientation):
    #     """
    #     Rotaciona os pontos da tile para a orientação especificada.
    #     orientation: int - Orientação da tile (0: sem rotação, 1: 90°, etc.).
    #     """
    #     angle = np.pi / 2 * orientation
    #     rotation_matrix = np.array([
    #         [np.cos(angle), -np.sin(angle)],
    #         [np.sin(angle), np.cos(angle)]
    #     ])
    #     return {
    #         side: np.dot(pts, rotation_matrix.T)
    #         for side, pts in points.items()
    #     }
