from socket import socket
from typing import NamedTuple
from numpy import ndarray, random, array_split, shape, array_equal, concatenate
from os import getcwd, path
from logging import Logger, shutdown
from time import perf_counter

MIN = 0
MAX = 5
LENGTH = 32
HORIZONTAL_PARTITIONS = 16
VERTICAL_PARTITIONS = 2
BUFFER = 4096
HEADERSIZE = 10
SIG_FIGS = 5
FILE_DIRECTORY_PATH = path.join(getcwd(), "project", "file")
FILENAME = "server_info.txt"
LOG_CONFIG_PATH = path.join(FILE_DIRECTORY_PATH, "logging", "log.conf")

class Address(NamedTuple):
    """
    Tuple defining IP Address and port

    Args:
        NamedTuple (str, int): IP Address and port
    """
    ip: str
    port: int

def partition_1(matrix_a: ndarray, matrix_b: ndarray, weights: list[float], log: Logger) -> tuple[list[ndarray], list[ndarray]]:
    # Start timer
    start = perf_counter()
    
    # Matrix A's width
    width = shape(matrix_a)[1]

    # Confirm Matrix A's width == Matrix B's length
    if width != shape(matrix_b)[0]:
        error_msg = "Matrix A and Matrix B are incompatible"
        log.error(error_msg)
        shutdown()
        raise ValueError(error_msg)

    # Each partition's (i.e. submatrix's) width (i.e. percentage * Matrix A's width)
    partition_widths = [ 1 if int(w * width) == 0 else int(w * width) for w in weights ]
    
    submatrices_a, submatrices_b, start, end = [], [], 0, 0

    # Split Matrix A and Matrix B into submatrices
    for w in partition_widths:
        end += start + w
        submatrices_a.append(matrix_a[:, start:end])
        submatrices_b.append(matrix_b[start:end, :])
        start = end

    # Confirm both submatrices are valid (i.e. combining submatrices_a == Matrix A && combining submatrices_b == Matrix B)
    if not array_equal(concatenate(submatrices_a, axis = 1), matrix_a) or not array_equal(concatenate(submatrices_b, axis = 0), matrix_b):
        # End timer
        end = perf_counter()
        error_msg = "Invalid submatrices... concatenated submatrices != original matrices"
        log.error(f"{error_msg}\n")
        log.info(f"Total runtime = {timing(end, start)} seconds")
        shutdown()
        raise ValueError(error_msg)

    # End timer
    end = perf_counter()
    log.info(f"Partitioned matrices in {timing(end, start)} seconds\n")
    
    return submatrices_a, submatrices_b

def partition(matrix_a: ndarray, matrix_b: ndarray, log: Logger) -> tuple[list[ndarray], list[ndarray]]:
    """
    Partition Matrix A and Matrix B into submatrices

    Args:
        matrix_a (ndarray): Matrix A to be partitioned
        matrix_b (ndarray): Matrix B to be partitioned
        logger (Logger): Logger to log messages

    Returns:
        tuple[list[ndarray], list[ndarray]]: Partitioned Matrix A and Matrix B
    """
    # Start timer
    start = perf_counter()
    
    # Split matrix horizontally
    sub_matrices = array_split(matrix_a, HORIZONTAL_PARTITIONS, axis = 0)

    # Split submatrices vertically
    partitions = [m for sub_matrix in sub_matrices for m in  array_split(sub_matrix, VERTICAL_PARTITIONS, axis = 1)], array_split(matrix_b, VERTICAL_PARTITIONS, axis = 0)

    # End timer
    end = perf_counter()
    log.info(f"Partitioned matrices in {timing(end, start)} seconds\n")
    
    return partitions

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