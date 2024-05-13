import pygame
import random


class Widgets:
    def __init__(self, img: pygame.surface.Surface, num: int, size: int):
        self.widgets = []
        self.img = img

        for widget in range(num):
            # setting the values on percent - the size might be changed
            scale = random.uniform(0.05, 0.3) * size
            speed = random.uniform(-3, 3)
            angle = random.randrange(360)

            rotated_img = pygame.transform.rotate(pygame.transform.scale(img, (scale, scale)), angle)

            pos = [random.uniform(0, 1), random.uniform(0, 1)]

            self.widgets.append([rotated_img, pos, [angle, speed]])

    def draw(self, surface: pygame.surface.Surface, size: tuple[int, int] | list[int, int]) -> None:
        # print each widget by [rotated image, pos (x, y), spin (angle, speed)]
        for widget in self.widgets:
            img = pygame.transform.rotate(widget[0], widget[2][0])
            surface.blit(img,  (widget[1][0] * size[0] - img.get_width() / 2, widget[1][1] * size[1] - img.get_height() / 2))
            self.widgets[self.widgets.index(widget)][2][0] += widget[2][1]

    def update(self, old_size: int, new_size: int) -> None:
        # update the scale of the widgets by the sizes of the screen
        for widget in self.widgets:
            scale = widget[0].get_width() * new_size / old_size
            self.widgets[self.widgets.index(widget)][0] = pygame.transform.scale(widget[0], (scale, scale))
