import numpy as np
from sympy import symbols, sympify

class TileDefinition:
    def __init__(self, name, equations, domains, sockets):
        """
        name: str - Name of the tile (e.g., 'straight', 'curved').
        equations: dict - Equations defining the track geometry.
        domains: dict - Domain intervals of the equations.
        sockets: dict - Connectivity definitions based on orientations.
        """
        self.name = name
        self.equations = equations  # Raw equations as strings
        self.domains = domains      # Domains of the equations
        self.sockets = sockets      # Connectivity rules
        self.parsed_equations = self.parse_equations(equations)  # Parsed equations

    def parse_equations(self, equations):
        """
        Converts equations defined as strings into usable functions.
        """
        parsed = {}
        x = symbols('x')
        for key, eq in equations.items():
            parsed[key] = sympify(eq)  # Convert to symbolic expression
        return parsed

    @classmethod
    def from_config(cls, config, global_params):
        """
        Creates a TileDefinition from a configuration (a single tile from the JSON file).
        """
        # Replace global parameters in equations
        equations = {
            key: eq.replace("tile_size", str(global_params['tile_size']))
                   .replace("track_width", str(global_params['track_width']))
            for key, eq in config['equations'].items()
        }

        # Replace global parameters in domains
        domains = {
            key: [
                float(sympify(limit.replace("tile_size", str(global_params['tile_size']))
                                        .replace("track_width", str(global_params['track_width']))))
                for limit in domain
            ]
            for key, domain in config.get("domains", {}).items()
        }

        return cls(config['name'], equations, domains, config['sockets'])

    def evaluate(self, orientation, global_params):
        """
        Generates points (numpy arrays) representing the track geometry based on the equations.
        """
        T = global_params.get('tile_size')
        points = {}

        for side, eq in self.parsed_equations.items():
            # Get the equation domain
            domain = self.domains.get(side, [0, T])
            domain_size = domain[1] - domain[0]

            # Adjust resolution proportionally to the domain size
            local_resolution = int(global_params["tile_resolution"] * (domain_size / T))

            # Generate x values within the domain
            x_vals = np.linspace(domain[0], domain[1], local_resolution)
            y_vals = [float(eq.evalf(subs={'x': x})) for x in x_vals]  # Evaluate the equation
            points[side] = np.column_stack((x_vals, y_vals))

        # Rotate the points according to the orientation
        if orientation:
            points = self.rotate_points(points, orientation, tile_size=T)

        return points

    def rotate_points(self, points, orientation, tile_size):
        """
        Rotates the tile points to the specified orientation around the tile center.
        orientation: int - Tile orientation (0: no rotation, 1: 90°, etc.).
        tile_size: float - Tile size (used to determine the rotation center).
        """
        angle = np.pi / 2 * orientation
        rotation_matrix = np.array([
            [np.cos(angle), np.sin(angle)],
            [-np.sin(angle), np.cos(angle)]
        ])

        # Tile center
        center = np.array([tile_size / 2, tile_size / 2])

        rotated_points = {}
        for side, pts in points.items():
            # Translate points to the center
            translated_pts = pts - center
            # Apply rotation
            rotated_pts = np.dot(translated_pts, rotation_matrix.T)
            # Translate back to the original position
            rotated_points[side] = rotated_pts + center

        return rotated_points

    def generate_bitmap(tile, global_params, grid_size=100, orientation=0):
        """
        Generates a bitmap for a single tile.

        tile: TileDefinition - Tile instance.
        global_params: dict - Global parameters, including tile_size.
        grid_size: int - Bitmap matrix size.
        orientation: int - Tile orientation (0, 1, 2, 3).

        Returns:
        np.ndarray - Tile bitmap.
        """
        
        tile_size = global_params.get('tile_size', 1)
        bitmap = np.zeros((grid_size, grid_size))  # Initialize empty bitmap

        # Scale to map the continuous space to the discrete grid
        scale = grid_size / tile_size

        # Generate points for the specified orientation
        points = tile.evaluate(orientation=orientation, global_params=global_params)

        # Map points to the bitmap
        for side, pts in points.items():
            for x, y in pts:
                # Convert continuous coordinates to bitmap indices
                i = int(y * scale)  # Row index
                j = int(x * scale)  # Column index
                if 0 <= i < grid_size and 0 <= j < grid_size:
                    bitmap[i, j] = 1  # Mark pixel as part of the track

        return bitmap
