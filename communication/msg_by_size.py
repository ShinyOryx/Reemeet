import socket
import rsa
from cryptography.fernet import Fernet

SIZE_HEADER_FORMAT = "00000000~"  # n digits for data size + one delimiter
size_header_size = len(SIZE_HEADER_FORMAT)


def recv_by_size(sock, key, symmetric=False, return_type="string", show=False):
    str_size = b""
    data_len = 0
    while len(str_size) < size_header_size:
        _d = sock.recv(size_header_size - len(str_size))
        if len(_d) == 0:
            str_size = b""
            break
        str_size += _d
    data = b""
    str_size = str_size.decode()
    if str_size != "":
        data_len = int(str_size[:size_header_size - 1])
        while len(data) < data_len:
            _d = sock.recv(data_len - len(data))
            if len(_d) == 0:
                data = b""
                break
            data += _d

    if data_len != len(data):
        data = b""  # Partial data is like no data !
    if symmetric:
        data = key.decrypt(data)
    elif key:
        data = rsa.decrypt(data, key)

    len_data = str(len(data)).zfill(size_header_size - 1) + "~"

    if show and len(len_data) > 0:
        data_to_print = data[:100]
        if type(data_to_print) == bytes:
            try:
                data_to_print = data_to_print.decode()
            except (UnicodeDecodeError, AttributeError):
                pass
        print(f"\nReceive({len_data})>>>{data_to_print}")

    if return_type == "string":
        return len_data + data.decode()
    return len_data.encode() + data


def send_with_size(sock, data, key, symmetric=False, show=False):

    if type(data) != bytes:
        data = data.encode()
    encrypted_data = data
    if symmetric:
        encrypted_data = key.encrypt(data)
    elif key:
        encrypted_data = rsa.encrypt(data, key)

    len_data = str(len(encrypted_data)).zfill(size_header_size - 1) + "~"
    len_data = len_data.encode()

    encrypted_data = len_data + encrypted_data
    sock.send(encrypted_data)

    if show and len(len_data) > 0:
        data = data[:100]
        if type(data) == bytes:
            try:
                data = data.decode()
            except (UnicodeDecodeError, AttributeError):
                pass
        print(f"\nSent({len_data})>>>{data}")
