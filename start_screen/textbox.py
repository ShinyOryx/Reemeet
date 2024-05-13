import pygame


# setting a text box which has features like writing, changing cursor and color
class TextBox:
    def __init__(self, pos: tuple[int, int] | list[int, int], size: tuple[int, int] | list[int, int],
                 color: tuple[int, int, int] | list[int, int, int],
                 bg_color: tuple[int, int, int] | list[int, int, int] | None = None):
        self.pos = pos
        self.box = pygame.Surface(size)
        self.size = size
        self.color = color
        self.font = pygame.font.SysFont('Ariel', int(size[1] * 1.2))
        self.bg_color = bg_color
        self.text = ''
        self.cursor = False
        self.lock = False
        self.cursor_pos = 0

        self.render_text()

    def resize(self, rect: tuple[int, int, int, int] | list[int, int, int, int]) -> None:
        self.pos = rect[0], rect[1]
        self.size = rect[2], rect[3]
        self.font = self.font = pygame.font.SysFont('Ariel', int(self.size[1] * 1.3))
        self.box = pygame.Surface(self.size)
        self.render_text()

    def render_text(self) -> None:
        # presents the text box
        text = self.font.render(self.text, False, self.color)
        self.box.fill(self.bg_color)
        self.box.blit(text, (5, 3))

        # show the cursor in the right place
        if self.cursor and (not self.lock or self.cursor_pos < len(self.text) or self.cursor_pos == 0):
            if self.text == '':
                part = 10
            else:
                part = self.font.render(self.text[:self.cursor_pos], False, (0, 0, 0)).get_width()
            self.box.blit(self.font.render('|', False, self.color), (part - 0.1 * self.size[1], 0))

    def limit(self, key: str):
        # checking if the surface has space for the next letter
        if self.font.render(self.text + key, False, (0, 0, 0)).get_width() > self.box.get_width():
            if not self.lock:
                self.lock = True
                if self.cursor:
                    self.cursor = False
        elif self.lock:
            self.lock = False

    def is_in_box(self, pos: tuple[int, int] | list[int, int]) -> bool:
        # checking if the click is in the text box
        in_box = pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1]).collidepoint(pos)
        if in_box:
            self.cursor = True
        else:
            self.cursor = False
            self.render_text()
        return in_box

    def find_by_pos(self, pos: tuple[int, int] | list[int, int]) -> None:
        # finding the letter which the mouse click on it in order to put there the cursor
        if not self.is_in_box(pos):
            return

        place = 0
        text = ''
        for letter in self.text:
            text += letter
            if pos[0] < self.pos[0] + self.font.render(text, False, (0, 0, 0)).get_width() - 0.2 * self.size[1]:
                self.cursor_pos = place
                break
            place += 1
        self.cursor_pos = place
        self.render_text()

    def update(self, let: str) -> None:
        # get a letter or a sign and checking text\adding\removing letters
        if len(self.text) > 0:
            if not self.cursor:
                self.cursor = True
            if let == 'backspace' and self.text[:self.cursor_pos] != '':
                self.text = self.text[:self.cursor_pos][:-1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
                if self.lock:  # if the surface was full, the cursor goes back
                    self.lock = False
            elif let == 'left':
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
            elif let == 'right':
                if self.cursor_pos < len(self.text):
                    self.cursor_pos += 1

        if let != 'backspace' and let != 'left' and let != 'right':
            self.limit(let)
            if not self.lock:
                if self.cursor_pos == -1:
                    self.text = let + self.text
                else:
                    self.text = self.text[:self.cursor_pos] + let + self.text[self.cursor_pos:]
                self.cursor_pos += 1

        self.render_text()





