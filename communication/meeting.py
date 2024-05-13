import pygame
from communication import client, video
import io


class Meeting:
    def __init__(self, surface: pygame.Surface, size: tuple | list, user: client, buttons: dict):
        self.surface = surface
        self.size = size
        self.user = user
        self.buttons = buttons

        self.screen = 0  # the index of the screen (in each screen - 4 participants)
        self.scale = None
        self.videos: list[video.Video] = []
        self.update()

    def scale_update(self):
        self.scale = self.size[0] * 0.45, self.size[0] * 0.3375  # 0.45 * window width * img height / img width
        if len(self.user.participants) == 1:
            self.scale = self.scale[0] * 0.8, self.scale[1] * 0.8
        elif len(self.user.participants) >= 2:
            self.scale = self.scale[0] * 0.6, self.scale[1] * 0.6

    def users_update(self):
        self.videos = []
        for user in self.user.participants:
            self.videos.append(video.Video(user, self.scale, self.user))

    def update(self, size: tuple | list = ()):
        if size:
            self.size = size
        self.scale_update()
        self.users_update()

    def client_show(self, space: float, y):
        if self.user.video and not self.user.hidden:
            user_camera = pygame.image.load(io.BytesIO(self.user.image))  # size[640x480]
            user_camera = pygame.transform.scale(user_camera, self.scale)
            self.surface.blit(user_camera, (space, y))
        else:
            font_size = 300
            while font_size > 20:
                name = pygame.font.SysFont('', font_size, False).render(self.user.name, False, (255, 255, 255))
                if name.get_width() < self.scale[0]:
                    break
                font_size -= 20
            pos = (self.scale[0] - name.get_width()) / 2, (self.scale[1] - name.get_height()) / 2
            self.surface.blit(name, (space + pos[0], y + pos[1]))
        pygame.draw.rect(self.surface, (255, 255, 255), (space, y, self.scale[0], self.scale[1]), 2)

    def buttons_show(self):
        # show the buttons in the bottom of the meeting screen
        pygame.draw.rect(self.surface, (20, 40, 60), [0, self.size[1] * 0.9, self.size[0], self.size[1] * 0.1])
        for button in self.buttons:
            s = pygame.Surface((button.get_width() / 2, button.get_height()), pygame.SRCALPHA)
            if list(self.buttons.keys()).index(button) == 0 and self.user.mute or list(self.buttons.keys()).index(
                    button) == 1 and self.user.deafen or \
                    list(self.buttons.keys()).index(button) == 2 and self.user.hidden:
                s.blit(button, (-self.buttons[button][2] / 2, 0))
            else:
                s.blit(button, (0, 0))
            self.surface.blit(s, (self.buttons[button].x, self.buttons[button].y))

    def buttons_update(self):
        # checking if one of the buttons is clicked
        for button in self.buttons:
            if self.buttons[button].collidepoint(pygame.mouse.get_pos()):
                button_kind = list(self.buttons.keys()).index(button)
                if button_kind == 0 and self.user.input:
                    self.user.mute = not self.user.mute
                elif button_kind == 1:
                    self.user.deafen = not self.user.deafen
                elif button_kind == 2 and self.user.video:
                    self.user.hidden = not self.user.hidden
                return

    def show(self):
        users = []
        for i in range(4):
            if i == 0 and self.screen == 0:
                users.append(1)
            elif self.screen * 4 + i > len(self.videos):
                break
            else:
                users.append(self.videos[self.screen * 4 + i - 1])
        space = self.get_space()
        if len(users) < 3:
            y = self.size[1] * 0.9 / 2
        else:
            y = self.size[1] * 0.9 / 4
        y -= self.scale[1] / 2

        self.buttons_show()
        width = space * 2 + self.scale[0] * 1
        for user in users:
            if type(user) == int:
                self.client_show(space, y)
            else:
                user.show(self.surface, (width, y))
                if users.index(user) != 2:
                    width = space
                    y += 1.1 * self.scale[1]
                else:
                    width = space * 2 + self.scale[0] * 1

    def get_space(self) -> float:
        # get the space between each video
        n = 2
        if self.videos:
            n += 1

        width = 0
        for i in range(n - 1):
            if width + self.scale[0] > self.size[0]:
                break
            width += self.scale[0]
        return (self.size[0] - width) / n
