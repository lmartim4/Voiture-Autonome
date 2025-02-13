import numpy as np
from sympy import symbols, sympify

class TileDefinition:
    def __init__(self, name, equations, domains, sockets):
        """
        name: str - Nom de la tuile (par exemple, 'straight', 'curved').
        equations: dict - Équations définissant la géométrie de la piste.
        domains: dict - Intervalles de domaine des équations.
        sockets: dict - Définition des connectivités basées sur les orientations.
        """
        self.name = name
        self.equations = equations  # Équations brutes sous forme de chaînes
        self.domains = domains      # Domaines des équations
        self.sockets = sockets      # Règles de connectivité
        self.parsed_equations = self.parse_equations(equations)  # Équations analysées

    def parse_equations(self, equations):
        """
        Convertit les équations définies en chaînes en fonctions utilisables.
        """
        parsed = {}
        x = symbols('x')
        for key, eq in equations.items():
            parsed[key] = sympify(eq)  # Convertit en expression symbolique
        return parsed

    @classmethod
    def from_config(cls, config, global_params):
        """
        Crée une TileDefinition à partir d'une configuration (une seule tuile dans le fichier JSON).
        """
        # Remplace les paramètres globaux dans les équations
        equations = {
            key: eq.replace("tile_size", str(global_params['tile_size']))
                   .replace("track_width", str(global_params['track_width']))
            for key, eq in config['equations'].items()
        }

        # Remplace les paramètres globaux dans les domaines
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
        Génère les points (tableaux numpy) de la géométrie de la piste à partir des équations.
        """
        T = global_params.get('tile_size')
        points = {}

        for side, eq in self.parsed_equations.items():
            # Obtenir le domaine de l'équation
            domain = self.domains.get(side, [0, T])
            domain_size = domain[1] - domain[0]

            # Ajuster la résolution proportionnellement à la taille du domaine
            local_resolution = int(resolution * (domain_size / T))

            # Générer les valeurs de x dans le domaine
            x_vals = np.linspace(domain[0], domain[1], local_resolution)
            y_vals = [float(eq.evalf(subs={'x': x})) for x in x_vals]  # Évaluer l'équation
            points[side] = np.column_stack((x_vals, y_vals))

        # Tourner les points selon l'orientation
        if orientation:
            points = self.rotate_points(points, orientation, tile_size=T)

        return points

    def rotate_points(self, points, orientation, tile_size):
        """
        Tourne les points de la tuile pour l'orientation spécifiée autour du centre de la tuile.
        orientation: int - Orientation de la tuile (0: pas de rotation, 1: 90°, etc.).
        tile_size: float - Taille de la tuile (utilisée pour déterminer le centre de rotation).
        """
        angle = np.pi / 2 * orientation
        rotation_matrix = np.array([
            [np.cos(angle), np.sin(angle)],
            [-np.sin(angle), np.cos(angle)]
        ])

        # Centre de la tuile
        center = np.array([tile_size / 2, tile_size / 2])

        rotated_points = {}
        for side, pts in points.items():
            # Translater les points vers le centre
            translated_pts = pts - center
            # Appliquer la rotation
            rotated_pts = np.dot(translated_pts, rotation_matrix.T)
            # Translater à nouveau pour revenir à la position originale
            rotated_points[side] = rotated_pts + center

        return rotated_points

    def generate_bitmap(tile, global_params, resolution=500, grid_size=100, orientation=0):
        """
        Génère un bitmap pour une seule tuile.

        tile: TileDefinition - Instance de la tuile.
        global_params: dict - Paramètres globaux, y compris tile_size.
        resolution: int - Résolution pour chaque tuile.
        grid_size: int - Taille de la matrice du bitmap.
        orientation: int - Orientation de la tuile (0, 1, 2, 3).

        Retourne:
        np.ndarray - Bitmap de la tuile.
        """
        
        tile_size = global_params.get('tile_size', 1)
        bitmap = np.zeros((grid_size, grid_size))  # Initialiser le bitmap vide

        # Échelle pour mapper l'espace continu au grid discret
        scale = grid_size / tile_size

        # Générer les points pour l'orientation spécifiée
        points = tile.evaluate(orientation=orientation, resolution=resolution, global_params=global_params)

        # Mapper les points sur le bitmap
        for side, pts in points.items():
            for x, y in pts:
                # Convertir les coordonnées continues en indices dans le bitmap
                i = int(y * scale)  # Indice de la ligne
                j = int(x * scale)  # Indice de la colonne
                if 0 <= i < grid_size and 0 <= j < grid_size:
                    bitmap[i, j] = 1  # Marque le pixel comme faisant partie de la piste

        return bitmap
