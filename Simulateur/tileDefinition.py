import numpy as np
from sympy import symbols, sympify

class TileDefinition:
    def __init__(self, name, equations, domains, sockets):
        """
        name: str - Nome da tile (e.g., 'straight', 'curved').
        equations: dict - Equações que definem a geometria da pista.
        domains: dict - Intervalos de domínio das equações.
        sockets: dict - Definições de conectividade com base nas orientações.
        """
        self.name = name
        self.equations = equations  # Raw equations como strings
        self.domains = domains      # Domínios das equações
        self.sockets = sockets      # Regras de conectividade
        self.parsed_equations = self.parse_equations(equations)  # Equações parseadas

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
        """
        # Substituir parâmetros globais nas equações
        equations = {
            key: eq.replace("tile_size", str(global_params['tile_size']))
                   .replace("track_width", str(global_params['track_width']))
            for key, eq in config['equations'].items()
        }

        # Substituir parâmetros globais nos domínios
        domains = {
            key: [
                float(sympify(limit.replace("tile_size", str(global_params['tile_size']))
                                        .replace("track_width", str(global_params['track_width']))))
                for limit in domain
            ]
            for key, domain in config.get("domains", {}).items()
        }

        return cls(config['name'], equations, domains, config['sockets'])

    def evaluate(self, orientation, global_params, resolution=100):
        """
        Gera os pontos (numpy arrays) da geometria da pista baseada nas equações.
        """
        T = global_params.get('tile_size')
        points = {}

        for side, eq in self.parsed_equations.items():
            # Obter o domínio da equação
            domain = self.domains.get(side, [0, T])
            domain_size = domain[1] - domain[0]

            # Ajustar a resolução proporcional ao tamanho do domínio
            local_resolution = int(resolution * (domain_size / T))

            # Gerar valores de x dentro do domínio
            x_vals = np.linspace(domain[0], domain[1], local_resolution)
            y_vals = [float(eq.evalf(subs={'x': x})) for x in x_vals]  # Avaliar a equação
            points[side] = np.column_stack((x_vals, y_vals))

        # Rotaciona os pontos de acordo com a orientação
        if orientation:
            points = self.rotate_points(points, orientation, tile_size=T)

        return points

    def rotate_points(self, points, orientation, tile_size):
        """
        Rotaciona os pontos da tile para a orientação especificada em torno do centro da tile.
        orientation: int - Orientação da tile (0: sem rotação, 1: 90°, etc.).
        tile_size: float - Tamanho da tile (usado para determinar o centro de rotação).
        """
        angle = np.pi / 2 * orientation
        rotation_matrix = np.array([
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)]
        ])

        # Centro da tile
        center = np.array([tile_size / 2, tile_size / 2])

        rotated_points = {}
        for side, pts in points.items():
            # Transladar os pontos para o centro
            translated_pts = pts - center
            # Aplicar rotação
            rotated_pts = np.dot(translated_pts, rotation_matrix.T)
            # Transladar de volta para a posição original
            rotated_points[side] = rotated_pts + center

        return rotated_points

