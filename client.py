import socket
import sys
import pygame

import rsa
from cryptography.fernet import Fernet
from communication.msg_by_size import recv_by_size, send_with_size
from communication import client, meeting
from start_screen import button, rect, textbox, widgets

# setting the client
connection = True
try:
    client_user = client.Client(('127.0.0.1', 60000))
    while True:
        # getting the public key and sending the symmetric key
        data = recv_by_size(client_user.client_sock, None, False, True, True)
        if data.split(b'~')[1] == b'PUBK':
            # setting the symmetric key
            key_bytes = Fernet.generate_key()
            symmetric_key = Fernet(key_bytes)
            send_with_size(client_user.client_sock, b'RETK~' + key_bytes, rsa.PublicKey.load_pkcs1(data.split(b'~')[2]),
                           False, True)
            break

except socket.error as err:
    print(err)
    connection = False
except Exception as err:
    print(err)
    connection = False

if connection:
    # set the window properties
    pygame.init()
    SIZE = [1200, 600]
    window = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
    icon = pygame.image.load(r'images/icon.png')
    pygame.display.set_icon(icon)
    pygame.display.set_caption('Reemeet')
    clock = pygame.time.Clock()


def texting_events(event: pygame.event.get, text_box: textbox.TextBox,
                   key: tuple[str, bool] | list[str, bool]) -> tuple[str, bool] | list[str, bool]:
    """
    :param event: the pygame event - for writing or changing cursor
    :param text_box: the text box which gets the changing
    :param key: the key which used to the long click
    :return: return the key to keep the key for the long click
    """
    # for setting the cursor by the mouse
    if event.type == pygame.MOUSEBUTTONDOWN:
        text_box.find_by_pos(pygame.mouse.get_pos())

    # for setting the timing for the showing of the cursor
    elif event.type == pygame.USEREVENT:
        text_box.cursor = not text_box.cursor
        text_box.render_text()

    # to determine if there is a long click
    elif event.type == pygame.USEREVENT + 1 and key[0] != '':
        key[1] = True

    elif event.type == pygame.KEYDOWN:
        if len(pygame.key.name(event.key)) == 1 and event.unicode != '^' or pygame.key.name(event.key) == 'space':
            key[0] = event.unicode  # space and each ascii key get the unicode key
            text_box.update(key[0])
            pygame.time.set_timer(pygame.USEREVENT, 0)
            pygame.time.set_timer(pygame.USEREVENT + 1, 500, 1)

        elif pygame.key.name(event.key) in 'backspace right left':
            key[0] = pygame.key.name(event.key)  # these keys get the name of them
            text_box.update(key[0])
            pygame.time.set_timer(pygame.USEREVENT, 0)
            pygame.time.set_timer(pygame.USEREVENT + 1, 500, 1)

    elif event.type == pygame.KEYUP:
        pygame.time.set_timer(pygame.USEREVENT, 500)  # to restart the cursor timing
        key = ['', False]  # to restart the long click

    return key


def disconnect():
    # closing the client sockets and the screen
    while True:
        try:
            send_with_size(client_user.client_sock, 'QUIT', symmetric_key, True, True)
            data = client_user.receiving_data(symmetric_key)
            if client_user.messages_protocol(symmetric_key, data) == 'QUIT':
                break
        except socket.error as err:
            print(err)
        except Exception as err:
            print(err)

    client_user.end_program = True
    client_user.__del__()
    pygame.quit()
    sys.exit()


def sign_up() -> str:
    # following the sign-up messages
    msg = client_user.receiving_data(symmetric_key)
    if msg[:4] == 'ERRR':
        send_with_size(client_user.client_sock, msg, symmetric_key, True, True)
    else:
        continue_to_meeting = client_user.messages_protocol(symmetric_key, msg)
        if continue_to_meeting == 'SIGN':
            return 'SIGN'
        if 'FAIL' in continue_to_meeting:
            pygame.time.set_timer(pygame.USEREVENT + 1, 5000, 1)
            return continue_to_meeting.split('~')[1]
    return 'ERRR'


def login() -> str:
    # following the log in messages
    msg = client_user.receiving_data(symmetric_key)
    if msg[:4] == 'ERRR':
        send_with_size(client_user.client_sock, msg, symmetric_key, True, True)
    else:
        continue_to_meeting = client_user.messages_protocol(symmetric_key, msg)
        if continue_to_meeting == 'LOGI':
            handle_client()
        elif 'FAIL' in continue_to_meeting:
            pygame.time.set_timer(pygame.USEREVENT + 1, 5000, 1)
            return continue_to_meeting.split('~')[1]
    return ''


def checking_user(name: textbox.TextBox, password: textbox.TextBox) -> str:
    # checking if the user has written username and passwd
    missing = ''
    if not name.text:
        missing = 'name'
    if not password.text:
        missing += 'pass'
    if missing:
        pygame.time.set_timer(pygame.USEREVENT + 1, 5000, 1)
    return missing


def main():
    global SIZE
    try:
        nbr = [SIZE[0] / 4, SIZE[1] / 3, SIZE[0] / 2, SIZE[1] / 10]  # nbr = name box rect
        name_box = textbox.TextBox([nbr[0], nbr[1]], [nbr[2], nbr[3]], (28, 21, 81), (206, 214, 255))
        name_frame = rect.Rect(nbr, (0, 0, 0), 5)
        name_text = pygame.font.SysFont('Ariel', int(nbr[3] * 1.3)).render('Username:', False, (255, 255, 255))

        pbr = [SIZE[0] / 4, SIZE[1] * 2 / 3, SIZE[0] / 2, SIZE[1] / 10]  # pbr = password box rect
        password_box = textbox.TextBox([pbr[0], pbr[1]], [pbr[2], pbr[3]], (28, 21, 81), (206, 214, 255))
        password_frame = rect.Rect(pbr, (0, 0, 0), 5)
        password_text = pygame.font.SysFont('Ariel', int(pbr[3] * 1.3)).render('Password:', False, (255, 255, 255))

        current_text_box = None
        pygame.time.set_timer(pygame.USEREVENT, 500)  # for the text box cursor
        key = ['', False]  # for long click - 1 is the key, 2 is if long click

        screen_widgets = widgets.Widgets(pygame.image.load('images/icon.png'), 10, SIZE[0])

        lbr = [SIZE[0] / 4, SIZE[1] * 5 / 6, SIZE[0] / 7, SIZE[1] / 10]  # lbr = login button rect
        login_button = button.Button([lbr[0], lbr[1]], [lbr[2], lbr[3]], (255, 255, 255), 'Log In', (40, 57, 163),
                                     (124, 136, 214))
        sbr = [SIZE[0] * 6.8 / 12, SIZE[1] * 5 / 6, SIZE[0] / 5.5, SIZE[1] / 10]  # sbr = sign up button rect
        signup_button = button.Button([sbr[0], sbr[1]], [sbr[2], sbr[3]], (255, 255, 255), 'Sign Up', (40, 57, 163),
                                      (124, 136, 214))

        title = pygame.font.SysFont('Ariel', int(SIZE[0] * 0.15)).render('Reemeet', False, (255, 255, 255))
        bold_title = pygame.font.SysFont('Ariel', int(SIZE[0] * 0.15)).render('Reemeet', False, (0, 0, 255))
        scaled_icon = pygame.transform.scale(icon, (SIZE[0] * 0.1, SIZE[0] * 0.1))

        login_click = False
        signup_click = False
        create_account = False

        signup_screen = pygame.Surface((SIZE[0] * 0.6, SIZE[1] * 0.85)).convert_alpha()
        signup_screen.fill((0, 54, 128, 220))
        signup_title = pygame.font.SysFont('Ariel', int(SIZE[0] * 0.1)).render('Sign Up', False, (255, 255, 255))

        missing = ''

        while True:
            window.fill((1, 31, 63))

            screen_widgets.draw(window, SIZE)
            window.blit(bold_title, (SIZE[0] * 0.33 - 2, SIZE[1] * 0.03 - 2))
            window.blit(bold_title, (SIZE[0] * 0.33 + 2, SIZE[1] * 0.03 - 2))
            window.blit(bold_title, (SIZE[0] * 0.33 - 2, SIZE[1] * 0.03 + 2))
            window.blit(bold_title, (SIZE[0] * 0.33 + 2, SIZE[1] * 0.03 + 2))
            window.blit(title, (SIZE[0] * 0.33, SIZE[1] * 0.03))
            window.blit(scaled_icon, (SIZE[0] * 0.23, SIZE[1] * 0.03))

            if signup_click:
                window.blit(signup_screen, (SIZE[0] * 0.2, SIZE[1] * 0.1))
                window.blit(signup_title, (SIZE[0] * 0.35, SIZE[1] * 0.1))

            # blit the text boxes on the window
            window.blit(name_box.box, name_box.pos)
            window.blit(name_text, (SIZE[0] / 4, SIZE[1] / 4))
            window.blit(password_box.box, password_box.pos)
            window.blit(password_text, (SIZE[0] / 4, SIZE[1] * 4 / 7))
            name_frame.draw(window)
            password_frame.draw(window)

            # blit the buttons - log in and sign up
            login_button.draw()
            signup_button.draw()
            window.blit(login_button.surface, login_button.pos)
            window.blit(signup_button.surface, signup_button.pos)

            if 'name' in missing:
                window.blit(pygame.font.SysFont('Ariel', int(nbr[3] * 0.8)).render('*You must enter a username!', False,
                                                                                   (255, 0, 0)), (nbr[0], nbr[1] * 1.3))
            if 'pass' in missing:
                window.blit(pygame.font.SysFont('Ariel', int(pbr[3] * 0.8)).render('*You must enter a password!', False,
                                                                                   (255, 0, 0)),
                            (pbr[0], pbr[1] * 1.15))
            elif missing == 'FAIL-PASS':
                window.blit(pygame.font.SysFont('Ariel', int(pbr[3] * 0.8)).render(f"*{fail_pass}", False, (255, 0, 0)),
                            (pbr[0], pbr[1] * 1.15))
            elif missing == 'FAIL-SIGN':
                window.blit(pygame.font.SysFont('Ariel', int(nbr[3] * 0.8)).render(f"*{fail_sign}", False, (255, 0, 0)),
                            (nbr[0], nbr[1] * 1.3))

            if key[1]:
                current_text_box.update(key[0])
                pygame.time.set_timer(pygame.USEREVENT, 0)

            if login_click:
                login_click = False
                fail_pass = login()
                if fail_pass:
                    missing = 'FAIL-PASS'

            if create_account:
                create_account = False
                fail_sign = sign_up()
                if fail_sign == 'SIGN':
                    signup_click = False
                    login_button.text = 'Log In'
                    signup_button.text = 'Sign Up'
                    if missing:
                        missing = ''
                elif fail_sign:
                    missing = 'FAIL-SIGN'

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    disconnect()

                elif event.type == pygame.USEREVENT + 1:
                    missing = ''

                elif event.type == pygame.VIDEORESIZE:
                    screen_widgets.update(SIZE[0], window.get_width())

                    SIZE = window.get_size()

                    title = pygame.font.SysFont('Ariel', int(SIZE[0] * 0.15)).render('Reemeet', False, (255, 255, 255))
                    bold_title = pygame.font.SysFont('Ariel', int(SIZE[0] * 0.15)).render('Reemeet', False, (0, 0, 255))
                    scaled_icon = pygame.transform.scale(icon, (SIZE[0] * 0.1, SIZE[0] * 0.1))

                    signup_screen = pygame.Surface((SIZE[0] * 0.6, SIZE[1] * 0.85)).convert_alpha()
                    signup_screen.fill((0, 54, 128, 220))
                    signup_title = pygame.font.SysFont('Ariel', int(SIZE[0] * 0.1)).render('Sign Up', False,
                                                                                           (255, 255, 255))

                    nbr = [SIZE[0] / 4, SIZE[1] / 3, SIZE[0] / 2, SIZE[1] / 10]
                    name_box.resize(nbr)
                    name_frame.rect = nbr
                    name_text = pygame.font.SysFont('Ariel', int(nbr[3] * 1.3)).render('Username:', False,
                                                                                       (255, 255, 255))
                    pbr = [SIZE[0] / 4, SIZE[1] * 2 / 3, SIZE[0] / 2, SIZE[1] / 10]
                    password_box.resize(pbr)
                    password_frame.rect = pbr
                    password_text = pygame.font.SysFont('Ariel', int(pbr[3] * 1.3)).render('Password:', False,
                                                                                           (255, 255, 255))

                    lbr = [SIZE[0] / 4, SIZE[1] * 5 / 6, SIZE[0] / 7, SIZE[1] / 10]
                    login_button.resize(lbr)
                    sbr = [SIZE[0] * 6.8 / 12, SIZE[1] * 5 / 6, SIZE[0] / 5.5, SIZE[1] / 10]
                    signup_button.resize(sbr)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # check which text box is used now (if there is) and set each text box by used or not
                    m_pos = pygame.mouse.get_pos()

                    if name_box.is_in_box(m_pos):
                        if current_text_box != name_box:
                            if 'name' or 'FAIL-PASS' in missing:
                                missing = missing[4:]
                            current_text_box = name_box
                            name_box.bg_color = 155, 226, 255
                            password_box.bg_color = 206, 214, 255
                            if password_box.cursor:
                                password_box.cursor = False
                            password_box.render_text()

                    elif password_box.is_in_box(m_pos):
                        if current_text_box != password_box:
                            if 'pass' or 'FAIL-PASS' in missing:
                                missing = missing[:-4]
                            current_text_box = password_box
                            password_box.bg_color = 155, 226, 255
                            name_box.bg_color = 206, 214, 255
                            if name_box.cursor:
                                name_box.cursor = False
                            name_box.render_text()

                    else:
                        if current_text_box is not None:
                            current_text_box = None
                            name_box.bg_color = 206, 214, 255
                            password_box.bg_color = 206, 214, 255
                            if name_box.cursor:
                                name_box.cursor = False
                            if password_box.cursor:
                                password_box.cursor = False
                            name_box.render_text()
                            password_box.render_text()

                if current_text_box is not None:
                    key = texting_events(event, current_text_box, key)

                if signup_button.is_clicked(event):
                    if signup_click:
                        missing = checking_user(name_box, password_box)
                        if not missing:
                            client_user.signup(symmetric_key, name_box.text, password_box.text)
                            create_account = True

                    else:
                        signup_click = True
                        name_box.text = password_box.text = missing = ''
                        name_box.render_text()
                        password_box.render_text()
                        login_button.text = 'Back'
                        signup_button.text = 'Done'

                elif login_button.is_clicked(event) and not login_click:
                    if signup_click:
                        signup_click = False
                        login_button.text = 'Log In'
                        signup_button.text = 'Sign Up'
                        if missing:
                            missing = ''
                    else:
                        missing = checking_user(name_box, password_box)
                        if not missing:
                            login_click = True
                            client_user.login(symmetric_key, name_box.text, password_box.text)

            pygame.display.update()
            clock.tick(240)

    except socket.error as err:
        print(err)
    except Exception as err:
        print(err)


def handle_client():
    global SIZE
    """
    this function connects between the client to the server (and the opposite).
    this function presents the GUI for the client and is ready for every client update.
    """
    try:
        send_with_size(client_user.client_sock, 'LIST', symmetric_key, True, True)
    except Exception as err:
        print(err)
        return

    b_scale = 0.08 * SIZE[0]

    buttons = {pygame.transform.scale(pygame.image.load(r'images/Meeting/un_mute.png'), (b_scale, b_scale * 0.65)):
                   pygame.Rect(SIZE[0] * 0.1, SIZE[1] * 0.9, b_scale, b_scale * 0.65),
               pygame.transform.scale(pygame.image.load(r'images/Meeting/un_deafen.png'), (b_scale, b_scale * 0.77)):
                   pygame.Rect(SIZE[0] * 0.3, SIZE[1] * 0.88, b_scale, b_scale * 0.77),
               pygame.transform.scale(pygame.image.load(r'images/Meeting/video.png'), (b_scale, b_scale * 0.77)):
                   pygame.Rect(SIZE[0] * 0.5, SIZE[1] * 0.88, b_scale, b_scale * 0.77)}

    meeting_screen = meeting.Meeting(window, SIZE, client_user, buttons)
    meeting_screen.update()

    while True:
        try:

            window.fill((1, 31, 63))

            if len(client_user.participants) != len(meeting_screen.videos):
                meeting_screen.update()
            meeting_screen.show()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    disconnect()

                elif event.type == pygame.VIDEORESIZE:
                    SIZE = window.get_size()
                    meeting_screen.update(SIZE)
                    buttons = {pygame.transform.scale(pygame.image.load(r'images/Meeting/un_mute.png'),
                                                      (b_scale, b_scale * 0.65)):
                                   pygame.Rect(SIZE[0] * 0.1, SIZE[1] * 0.9, b_scale, b_scale * 0.65),
                               pygame.transform.scale(pygame.image.load(r'images/Meeting/un_deafen.png'),
                                                      (b_scale, b_scale * 0.77)):
                                   pygame.Rect(SIZE[0] * 0.3, SIZE[1] * 0.88, b_scale, b_scale * 0.77),
                               pygame.transform.scale(pygame.image.load(r'images/Meeting/video.png'),
                                                      (b_scale, b_scale * 0.77)):
                                   pygame.Rect(SIZE[0] * 0.5, SIZE[1] * 0.88, b_scale, b_scale * 0.77)}
                    meeting_screen.buttons = buttons

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    meeting_screen.buttons_update()

            pygame.display.update()
            clock.tick(60)

        except Exception as err:
            print(err)


if __name__ == "__main__":
    if connection:
        main()
