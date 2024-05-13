import pygame
from communication import client
import io


class Video:
    def __init__(self, name: str, scale: tuple[int, int] | list[int, int], user: client):
        self.name = name
        self.scale = scale
        self.user = user

        self.text = None
        font_size = 300
        while font_size > 20:
            self.text = pygame.font.SysFont('', font_size, False).render(name, False, (255, 255, 255))
            if self.text.get_width() < scale[0]:
                break
            font_size -= 20
        self.text_pos = (self.scale[0] - self.text.get_width()) / 2, (self.scale[1] - self.text.get_height()) / 2

    def show(self, surface: pygame.Surface, pos: tuple | list) -> None:
        if self.name in self.user.clients_images:
            if self.user.clients_images[self.name]:
                try:
                    user_camera = pygame.image.load(io.BytesIO(self.user.clients_images[self.name]))  # size[640x480]
                    user_camera = pygame.transform.scale(user_camera, self.scale)
                    surface.blit(user_camera, pos)
                except:
                    surface.blit(self.text, (pos[0] + self.text_pos[0], pos[1] + self.text_pos[1]))
            else:
                surface.blit(self.text, (pos[0] + self.text_pos[0], pos[1] + self.text_pos[1]))
        else:
            surface.blit(self.text, (pos[0] + self.text_pos[0], pos[1] + self.text_pos[1]))
        pygame.draw.rect(surface, (255, 255, 255), (pos[0], pos[1], self.scale[0], self.scale[1]), 2)
