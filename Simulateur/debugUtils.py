import numpy as np
import matplotlib.pyplot as plt

# Drapeau pour décider s'il faut imprimer les arrays
PRINT_POINTS = False

def inspectTile(tile_name, resolution, thickness, orientation, tile_definitions, global_params):
    """
    Inspecte une tuile spécifique et génère son bitmap.

    tile_name: str - Nom de la tuile à inspecter.
    resolution: int - Résolution pour chaque tuile.
    thickness: int - Épaisseur de la piste dans le bitmap.
    orientation: int - Orientation de la tuile (0, 1, 2, 3).
    tile_definitions: list - Liste des instances de TileDefinition.
    global_params: dict - Paramètres globaux, y compris tile_size.

    Retourne:
    None
    """
    # Trouver la tuile par son nom
    tile = next((t for t in tile_definitions if t.name == tile_name), None)
    if tile is None:
        print(f"Tuile '{tile_name}' non trouvée.")
        return

    print(f"Inspection de la tuile: {tile_name}")
    print(f"Orientation: {orientation * 90}°")
    print(f"Résolution: {resolution}")
    print(f"Épaisseur: {thickness}")

    # Générer le bitmap
    grid_size = 200  # Taille fixe pour le bitmap
    bitmap = generate_bitmap(tile, global_params, resolution=resolution, grid_size=grid_size, orientation=orientation)

    # Imprimer les points si le drapeau est actif
    if PRINT_POINTS:
        points = tile.evaluate(orientation=orientation, resolution=resolution, global_params=global_params)
        for side, pts in points.items():
            print(f"  {side}: {pts}")

    # Afficher le bitmap
    plt.imshow(bitmap, cmap='Greys', origin='lower')
    plt.title(f"Bitmap de la tuile: {tile_name} | Orientation: {orientation * 90}°")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.show()