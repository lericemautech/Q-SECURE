from socket import socket
from typing import NamedTuple
from numpy import ndarray, random

MIN = 0
MAX = 5
LENGTH = 16
MATRIX_2_WIDTH = 2
HORIZONTAL_PARTITIONS = 2
VERTICAL_PARTITIONS = 2
BUFFER = 4096
HEADERSIZE = 10

class Address(NamedTuple):
    """
    Tuple defining IP Address and port

    Args:
        NamedTuple (str, int): IP Address and port
    """
    ip: str
    port: int

def send(sock: socket, data: bytes) -> None:
    """
    Send data to socket

    Args:
        sock (socket): Connected socket
        data (bytes): Data to be sent
    """
    # Add header to data packet
    data_with_header = bytes(f"{len(data):<{HEADERSIZE}}", "utf-8") + data

    # Send data packet to socket
    sock.sendall(data_with_header)

def receive(sock: socket) -> bytes:
    """
    Receive data from socket

    Args:
        sock (socket): Connected socket

    Returns:
        bytes: Received data
    """
    data, new_data, msg_length = b"", True, 0
    
    # Receive result from socket
    while True:
        packet = sock.recv(BUFFER)
        if not packet:
            break
        data += packet

        # Check if entire message has been received
        if new_data:
            msg_length = int(data[:HEADERSIZE])
            new_data = False

        if len(data) - HEADERSIZE >= msg_length:
            break

    # Remove header from data packet, then return
    return data[HEADERSIZE:HEADERSIZE + msg_length]

def generate_matrix(length: int, width: int) -> ndarray:
    """
    Generates a random matrix of size length * width

    Args:
        length (int): Length of matrix
        width (int): Width of matrix

    Returns:
        ndarray: Random matrix of size length * width
    """
    return random.randint(MIN, MAX, size = (length, width), dtype = int)