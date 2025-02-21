import pygame

class Environment:
    
    black = (0, 0, 0)
    white = (255, 255, 255)

    def __init__(self, map_name, max_size=800, padding_percent=0.05):
        """
        Initializes the simulation environment.

        :param map_name: str, Name of the map file inside 'tracks/' folder.
        :param max_size: int, Maximum size (either width or height).
        :param padding_percent: float, Percentage of the max_size to be used as padding.
        """
        pygame.init()

        # Load external map
        self.external_map = pygame.image.load(f'tracks/{map_name}')

        # Get original dimensions
        orig_width, orig_height = self.external_map.get_width(), self.external_map.get_height()

        # Compute the scale factor while keeping aspect ratio
        scale_factor = min(max_size / orig_width, max_size / orig_height)

        # Compute new dimensions after scaling
        new_width, new_height = int(orig_width * scale_factor), int(orig_height * scale_factor)

        # Compute padding based on max_size and the given percentage
        padding = int(max_size * padding_percent)

        # Compute final window dimensions including padding
        final_width = new_width + 2 * padding
        final_height = new_height + 2 * padding

        # Create window
        pygame.display.set_caption(f"Simulation - Map: {map_name}")
        self.map = pygame.display.set_mode((final_width, final_height))

        # Fill background with white
        self.map.fill(self.white)

        # Compute position to center the image with padding
        x_offset = (final_width - new_width) // 2
        y_offset = (final_height - new_height) // 2

        # Scale the image and draw it on the screen
        self.external_map = pygame.transform.scale(self.external_map, (new_width, new_height))
        self.map.blit(self.external_map, (x_offset, y_offset))

    def run(self):
        """Main loop to keep the window open."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            pygame.display.update()

        pygame.quit()
