import pygame


class Button:
    def __init__(self, pos: tuple[int, int] | list[int, int], size: tuple[int, int] | list[int, int],
                 color: tuple[int, int, int] | list[int, int, int], text: str,
                 click_color: tuple[int, int, int] | list[int, int, int] | None = None,
                 bg_color: tuple[int, int, int] | list[int, int, int] | None = None):
        self.pos = pos
        self.size = size
        self.color = color
        self.text = text
        self.click_color = click_color
        self.bg_color = bg_color

        self.surface = pygame.Surface(size)
        self.font = pygame.font.SysFont('Ariel', int(size[1] * 1.2))

    def draw(self) -> None:
        # if the mouse is on the button
        if pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1]).collidepoint(pygame.mouse.get_pos()):
            self.surface.fill(self.click_color)
            text = self.font.render(self.text, False, self.color)
            self.surface.blit(text, (0, 0))
        else:
            self.surface.fill(self.bg_color)
            text = self.font.render(self.text, False, self.color)
            self.surface.blit(text, (0, 0))

    def resize(self, rect: tuple[int, int, int, int] | list[int, int, int, int]) -> None:
        self.pos = rect[0], rect[1]
        self.size = rect[2], rect[3]
        self.font = self.font = pygame.font.SysFont('Ariel', int(self.size[1] * 1.3))
        self.surface = pygame.Surface(self.size)
        self.draw()

    def is_clicked(self, event: pygame.event.get):
        return event.type == pygame.MOUSEBUTTONDOWN and\
            pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1]).collidepoint(pygame.mouse.get_pos())
