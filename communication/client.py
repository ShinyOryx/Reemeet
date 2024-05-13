import socket
import threading
import pyaudio
import cv2
import time

from communication.msg_by_size import recv_by_size, send_with_size


class Client:
    def __init__(self, host_addr: tuple[str, int] | list[str, int]):
        # the socket for the client, its audio and its video
        self.server = host_addr
        self.client_sock = socket.socket()
        self.client_sock.connect(host_addr)

        self.audio_video_sock = None  # for the meeting
        self.udp_addr = None
        self.name = None  # name of client (in the meeting)
        self.participants = None

        self.lock = threading.Lock()

        # make an audio system - input and output and a video system - camera
        try:
            self.input = pyaudio.PyAudio().open(
                format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
            self.mute = False
        except:  # if there is not an input
            self.input = None
        try:
            self.output = pyaudio.PyAudio().open(
                format=pyaudio.paInt16, channels=1, rate=44100, output=True, frames_per_buffer=1024)
            self.deafen = False
        except:  # if there is not an input
            self.output = None
        self.video = cv2.VideoCapture(0)
        self.hidden = not self.video.read()[0]
        if not self.hidden:
            self.image = b''
        else:
            self.video = None

        self.clients_images = {}
        # for closing the threads in the meeting ending
        self.end_program = False

    def __del__(self):
        try:
            self.client_sock.close()
            self.audio_video_sock.close()
        except AttributeError:
            pass

    def messages_protocol(self, key, msg: str) -> str:
        """
        :param msg: the message for analysis
        checking the code message and sending the message to the server
        """
        try:
            code = msg.split('~')[0]

            if code == 'OKAY':
                msg_type = msg.split('~')[1]
                if msg_type == 'LOGI':
                    self.set_meeting_connection(int(msg.split('~')[2]))
                    return 'LOGI'
                elif msg_type == 'SIGN':
                    return 'SIGN'
                elif msg_type == 'QUIT':
                    return 'QUIT'
                return 'LIST'
            elif code == 'FAIL':
                return msg
            elif code == 'ERRR':
                print(msg.split('~')[1])

            else:
                send_with_size(self.client_sock, 'ERRR~2 Header Error: The message code does not exist.', key, True, True)

        except Exception as err:
            send_with_size(self.client_sock, f'ERRR~3 Message Error: There is a problem with the message analysis: {err}', key, True, True)
        return ''

    @staticmethod
    def checking_message(msg: bytes) -> str:
        try:
            parts = msg.split(b'~')  # split the message to fields
            ret_err = ''

            # find any error in the message header
            if len(parts) < 3:
                ret_err = 'The message does not have all the required fields.'

            elif len(parts[0]) != 8:
                ret_err = 'The size field was sent wrongly.'

            elif int(parts[0]) != len(msg[9:]):
                ret_err = 'The size of the size field is not equal to the size of the message.'

            elif len(parts[1]) != 4:
                ret_err = 'The message code length must contains only 4 bytes.'

            if ret_err:
                return 'ERRR~2 Header Error: ' + ret_err
            return ''

        except ValueError:
            return 'ERRR~2 Header Error: The size header can\'t be integer.'
        except Exception as err:
            return f'ERRR~3 Message Error: There is a problem with the message analysis: {err}'

    def receiving_data(self, key):
        # receiving data and checking for errors
        try:
            data = recv_by_size(self.client_sock, key, True, 'bytes', True)
            err = self.checking_message(data)
            if err:
                return err
            return data[9:].decode()
        except socket.error as err:
            print(err)
            return f'ERRR~1 Connection Error: There is a problem with connection: {err}'

    def login(self, key, username: str, password: str):
        """
        :param key: the symmetric key for encryption
        :param username: the username of the client
        :param password: the password of the client
        sending the username and the password in order to log in
        """
        try:
            msg = f'LOGI~{username}^^^{password}'
            send_with_size(self.client_sock, msg, key, True, True)
            self.name = username
        except socket.error as err:
            print(err)

    def signup(self, key, username: str, password: str):
        """
        :param key: the symmetric key for encryption
        :param username: the username of the client
        :param password: the password of the client
        sending the username and the password in order to sign up
        """
        try:
            msg = f'SIGN~{username}^^^{password}'
            send_with_size(self.client_sock, msg, key, True, True)
        except socket.error as err:
            print(err)

    def set_meeting_connection(self, port: int):
        # setting the udp socket for the meeting
        self.audio_video_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_addr = '0.0.0.0', port
        self.audio_video_sock.bind(self.udp_addr)

        if self.input:
            threading.Thread(target=self.send_audio, args=()).start()
        if self.video:
            threading.Thread(target=self.send_video, args=()).start()
        threading.Thread(target=self.receive_data, args=()).start()

    def receive_data(self):
        """
        receiving the data from the server by the code of the message.
        the code of the message is the first four letters of the message.
        """
        while True:
            try:
                if self.end_program:
                    break
                data, addr = self.audio_video_sock.recvfrom(65535)
                name = data.split(b'~')[1].decode()
                msg = data[6 + len(name):]  # the content of the data without the code and the name

                if data[:5] == b'LIST~':
                    self.participants: list = data[5:].decode().split('~')
                    self.participants.pop(self.participants.index(self.name))
                if data[:5] == b'ADIO~' and self.output:
                    if not self.deafen:
                        self.output.write(msg[:2048])
                elif data[:5] == b'STVD~':
                    self.clients_images[name] = msg
                    if data[-5:] == b'~ENVD':
                        self.clients_images[name] = self.clients_images[name][:-5]
                elif data[:5] == b'CNVD~':
                    self.clients_images[name] += msg
                    if data[-5:] == b'~ENVD':
                        self.clients_images[name] = self.clients_images[name][:-5]

            except socket.error as err:
                print(err)
            except Exception as err:
                print('#1', err)

    def send_data(self, data: bytes):
        """
        :param data: the data of the message which need to send.
        locking the function in order to keep the program from threading crisis
        and releasing in the end of the sending.
        """
        try:
            if self.end_program:
                return

            self.lock.acquire()
            self.audio_video_sock.sendto(data, self.server)
            self.lock.release()

        except Exception as err:
            print('#2', err)
            return

    def send_audio(self):
        """
        taking the data from the input stream and read 1024 bytes from it.
        then send the bytes as a message in to the send function with the message code ('ADIO').
        """
        while True:
            try:
                if self.end_program:
                    break

                if not self.mute:
                    data = self.input.read(1024)
                    self.send_data(b'ADIO~' + str(self.name).encode() + b'~' + data)
                else:
                    time.sleep(0.01)

            except Exception as err:
                print('#3', err)

    def send_video(self):
        """
        taking the image from the camera and slicing it into parts of 65531 bytes in order
        to send it - (the image is too long). the message will be like that:
        the first part has a message code ('STVD') and the other message has a different
        message code ('CNVD') in order to know that all the message are one image.
        the last part of the image has another code ('ENVD') - to know the end of the image.
        """
        hide = False
        while True:
            try:
                if self.end_program:
                    break

                if self.hidden:
                    if not hide:
                        self.send_data(b'STVD~' + self.name.encode() + b'~~ENVD')  # sends b'' to hide camera
                        hide = True
                else:
                    if hide:
                        hide = False
                    # taking the image from the camera into bytes
                    self.image = cv2.imencode('.jpg', cv2.flip(self.video.read()[1], 1))[1].tobytes()

                    # slicing the image bytes into parts in order to send it
                    n = int(len(self.image) / 65450)
                    for i in range(1, n + 2):
                        if i == 1:
                            msg = b'STVD~' + str(self.name).encode() + b'~' +\
                                  self.image[:65450 - len(str(self.name))]
                        else:
                            msg = b'CNVD~' + str(self.name).encode() + b'~' +\
                                  self.image[(65450 - len(str(self.name))) * (i - 1): (65450 - len(str(self.name))) * i]
                        if i == n + 1:
                            self.send_data(msg + b'~ENVD')
                        else:
                            self.send_data(msg)
                time.sleep(0.01)

            except Exception as err:
                print(err)
