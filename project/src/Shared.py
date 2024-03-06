from socket import socket
from typing import NamedTuple
from numpy import ndarray, random
from os import getcwd, path
from logging.config import fileConfig

"""Matrix Parameters"""
MIN = 0
MAX = 5
LENGTH = 32
SIG_FIGS = 5

"""Partition Parameters"""
HORIZONTAL_PARTITIONS = 16
VERTICAL_PARTITIONS = 2

"""Socket Parameters"""
BUFFER = 4096
HEADERSIZE = 10
ACKNOWLEDGEMENT = "ACK"

"""File Directory Path"""
FILE_DIRECTORY_PATH = path.join(getcwd(), "project", "file")

"""Server Info Parameters"""
MAX_NUM_FILES = 10
FILEPATH = path.join(FILE_DIRECTORY_PATH, "server_info", "server_info.txt")

"""SSL/TLS Parameters"""
KEYS_DIRECTORY_PATH = path.join(FILE_DIRECTORY_PATH, "keys")
CLIENT_CERT = path.join(KEYS_DIRECTORY_PATH, "client.crt")
CLIENT_KEY = path.join(KEYS_DIRECTORY_PATH, "client.key")
SERVER_CERT = path.join(KEYS_DIRECTORY_PATH, "server.crt")
SERVER_KEY = path.join(KEYS_DIRECTORY_PATH, "server.key")

class Address(NamedTuple):
    """
    Tuple defining IP Address and port

    Args:
        NamedTuple (str, int): IP Address and port
    """
    ip: str
    port: int

# TODO Relocate SERVER_ADDRESSES to separate file for improved security and editing
SERVER_ADDRESSES = [ Address("127.0.0.1", 12345), Address("127.0.0.1", 12346), Address("127.0.0.1", 12347) ]
#SERVER_ADDRESSES = [ Address("192.168.207.129", 12345), Address("192.168.207.130", 12346), Address("192.168.207.131", 12347) ]

def create_logger(log_name: str) -> None:
    fileConfig(path.join(FILE_DIRECTORY_PATH, "logging", "log.conf"), defaults = { "logfilename" : log_name, "dirpath" : FILE_DIRECTORY_PATH }, disable_existing_loggers = False)

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
    return (data[HEADERSIZE:HEADERSIZE + msg_length])

def timing(end: float, start: float) -> float:
    """
    Convenience method for timing

    Args:
        end (float): End time (seconds)
        start (float): Start time (seconds)

    Returns:
        float: Time elapsed (seconds), rounded to SIG_FIGS significant figures
    """
    return round(end - start, SIG_FIGS)

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