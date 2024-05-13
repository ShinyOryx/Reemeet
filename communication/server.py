import socket
import threading
import time


class MeetingServer:
    def __init__(self, addr: tuple[str, int] | list[str, int]):
        self.addr = addr
        self.users = {}
        self.users_audio = {}
        self.users_video = {}

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(addr)
        threading.Thread(target=self.receive_data).start()
        threading.Thread(target=self.send_data).start()

    def insert_user(self, name: str, user_addr: tuple[str, int] | list[str, int]):
        self.users[name] = user_addr
        self.users_audio[user_addr] = None
        self.users_video[user_addr] = [None, None]

    def update_users(self):
        for user in self.users.values():
            try:
                self.sock.sendto(f'LIST~{"~".join(list(self.users))}'.encode(), user)
                print(f'sent to {user} >>> LIST~{"~".join(list(self.users))}')
            except socket.error as err:
                print(err)

    def remove_user(self, user_addr: tuple[str, int] | list[str, int]):
        self.users.pop(list(self.users.keys())[list(self.users.values()).index(user_addr)])
        self.users_audio.pop(user_addr)
        self.users_video.pop(user_addr)
        self.update_users()

    def receive_data(self):
        """
        receiving the data from clients by the code of the message.
        the code of the message is the first four letters of the message.
        setting the messages by two dicts of audio and video by each client.
        """
        while True:
            try:
                data, addr = self.sock.recvfrom(65535)
                if data[:5] == b'ADIO~':
                    self.users_audio[addr] = data[:2053]
                elif data[:5] == b'STVD~':
                    self.users_video[addr][0] = data
                elif data[:5] == b'CNVD~':
                    self.users_video[addr][1] = data

            except socket.error as err:
                print(err)
            except Exception as err:
                print(err)

    def send_data(self):
        """
        the server sends data to client from each client - audio and video.
        Each client won't receive his message.
        initializing the messages of the clients after the sending.
        """
        while True:
            try:
                if self.users:
                    # sending audio to the clients
                    for client in self.users_audio:
                        if self.users_audio[client] is not None:
                            for user in self.users.values():
                                if user != client:
                                    self.sock.sendto(self.users_audio[client], user)
                        self.users_audio[client] = None
                    # sending video to the clients
                    for client in self.users_video:
                        if self.users_video[client][0] is not None:
                            for user in self.users.values():
                                if user != client:
                                    self.sock.sendto(self.users_video[client][0], user)
                                    if self.users_video[client][1] is not None:
                                        self.sock.sendto(self.users_video[client][1], user)
                        self.users_video[client] = [None, None]
                    else:
                        time.sleep(0.01)

            except socket.error as err:
                print(err)

            except Exception as err:
                print(err)
