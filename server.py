import socket
import threading

from communication.msg_by_size import recv_by_size, send_with_size
from communication import server
import rsa
from cryptography.fernet import Fernet
import hashlib
import pymongo

# initializing the server of the meeting
connection = True
ADDR = '0.0.0.0', 60000
try:
    meeting_server = server.MeetingServer(ADDR)
except socket.error as err:
    print(err)
    connection = False
except Exception as err:
    print(err)
    connection = False

if connection:
    # pymongo variables
    mongo_db = pymongo.MongoClient('mongodb://localhost:27017/')
    db = mongo_db['Zoom']
    users = db.zoom['accounts']

    # generate a key for encryption
    public_key, private_key = rsa.newkeys(512)
    public_key_bytes = public_key.save_pkcs1()  # convert public key to bytes for sending
    tcp_clients = {}
    udp_clients = {}


def checking_message(msg: bytes, addr: tuple[str, int] | list[str, int]) -> str:
    try:
        parts = msg.split(b'~')  # split the message to fields
        ret_err = ''

        # find any error in the message header
        if len(parts) < 2:
            ret_err = 'The message does not have all the required fields.'

        elif len(parts[0]) != 8:
            ret_err = 'The size field was sent wrongly.'

        elif int(parts[0]) != len(msg[9:]):
            ret_err = 'The size of the size field is not equal to the size of the message.'

        elif len(parts[1]) != 4:
            ret_err = 'The message code length must contains only 4 bytes.'

        if ret_err:
            return 'ERRR~2 Header Error: ' + ret_err
        return request_protocol(msg[9:], addr)

    except Exception as err:
        return f'ERRR~3 Message Error: There is a problem with the message analysis: {err}'


def request_protocol(data: bytes, addr: tuple[str, int] | list[str, int]) -> str:
    """
    :param addr: the address of the client - to send it to the client socket for the meeting.
    :param data: the message without the size header
    :return: the message for sending to the client according to client message
    """
    global udp_clients
    try:
        code = data.split(b'~')[0].decode()

        if code == 'RETK':  # symmetric key
            return Fernet(data.split(b'~')[1])

        elif code == 'LOGI':
            username, password = data[5:].decode().split('^^^')
            user = users.find_one({'username': username})
            if not user:
                return f'FAIL~Username or password is incorrect.'
            # comparing the given password to the user password
            hashed_pass = hashlib.sha256(password.encode()).hexdigest()
            stored_hashed_pass = user['password']
            if hashed_pass == stored_hashed_pass:
                meeting_server.insert_user(username, addr)
                return f'OKAY~LOGI~{addr[1]}'
            return 'FAIL~Username or password is incorrect.'
        elif code == 'SIGN':
            username, password = data[5:].decode().split('^^^')
            user = users.find_one({'username': username})
            if user:
                return f"FAIL~The name '{username}' is occupied."
            new_user = {'username': username, 'password': hashlib.sha256(password.encode()).hexdigest()}
            new_user = users.insert_one(new_user)
            if new_user.inserted_id:
                return 'OKAY~SIGN'
            else:
                return 'FAIL-Failed to create user.'

        elif code == 'LIST':
            meeting_server.update_users()
            return ''

        elif code == 'QUIT':
            return 'OKAY~QUIT'

        elif code == 'ERRR':
            print(data.split(b'~')[1].decode())

        else:
            return 'ERRR~2 Header Error: The message code does not exist.'

    except Exception as err:
        return f'ERRR~3 Message Error: There is a problem with the message analysis: {err}'


def handle_client(addr: tuple[str, int] | list[str, int], sock) -> None:
    """
    :param addr: the address of the client (ip, port)
    :param sock: the socket of the client - to receive and send messages
    connection between the socket and the client
    """
    global tcp_clients

    try:
        while True:
            # make sure the client is getting the public key and receive the symmetric key from the client
            send_with_size(sock, b'PUBK~' + public_key_bytes, None, False, True)
            data = recv_by_size(sock, private_key, False, 'bytes', True)
            if data.split(b'~')[1] == b'RETK':
                symmetric_key = checking_message(data, addr)
                break

        while True:
            data = recv_by_size(sock, symmetric_key, True, 'bytes', True)
            if data == b'':
                break

            to_send = checking_message(data, addr)
            if to_send:
                send_with_size(sock, to_send, symmetric_key, True, True)

            if data.split(b'~')[1] == b'QUIT' and to_send == 'OKAY~QUIT':
                break

    except socket.error as err:
        print(err)
    except Exception as err:
        print(err)

    tcp_clients.pop(addr)
    try:
        sock.close()
        meeting_server.remove_user(addr)
    except socket.error:
        pass
    except ValueError:
        pass
    print(f'The client {addr} has disconnected.')


def main() -> None:
    global tcp_clients

    # create a socket on port 60000
    serv_sock = socket.socket()
    serv_sock.bind(ADDR)
    serv_sock.listen(20)  # limit - until 20 participants in a meeting

    print('Waiting for clients...')
    while True:
        # accepting new clients (until the limited number)
        if len(tcp_clients) < 21:
            try:
                client_sock, client_addr = serv_sock.accept()
                print(f'>>>There is a connection from {client_addr}')
                tcp_clients[client_addr] = client_sock
                threading.Thread(target=handle_client, args=(client_addr, client_sock)).start()
            except Exception as err:
                print('#1', err)


if __name__ == "__main__":
    if connection:
        main()
