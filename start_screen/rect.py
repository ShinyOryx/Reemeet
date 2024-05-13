import pygame


# saving a rect with the rect features and blit it on the surface
class Rect:
    def __init__(self, rect: tuple[int, int, int, int] | list[int, int, int, int],
                 color: tuple[int, int, int] | list[int, int, int], width: int):
        self.rect = rect
        self.color = color
        self.width = width

    def draw(self, surface: pygame.surface.Surface) -> None:
        pygame.draw.rect(surface, self.color, self.rect, self.width)
