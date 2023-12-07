from socket import socket
from typing import NamedTuple
from numpy import ndarray, random, array_equal, concatenate

TIMEOUT = 10
BUFFER = 4096
HEADERSIZE = 10
MIN = 0
MAX = 5
LENGTH = 16
MATRIX_2_WIDTH = 2
HORIZONTAL_PARTITIONS = 2
VERTICAL_PARTITIONS = 2

class Matrix(NamedTuple):
    matrix: ndarray
    index: int

class Address(NamedTuple):
    ip: str
    port: int

def add_header(data: bytes) -> bytes:
    """
    Add header to data

    Args:
        data (bytes): Data to be sent

    Returns:
        bytes: Data with header
    """
    return bytes(f"{len(data):<{HEADERSIZE}}", "utf-8") + data

def send_data(sock: socket, data: bytes) -> None:
    """
    Send data to socket

    Args:
        sock (socket): Connected socket
        data (bytes): Data to be sent
    """
    # Add header to data packet
    data_with_header = add_header(data)

    # Send message back
    sock.sendall(data_with_header)

def receive_data(sock: socket) -> bytes:
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
    return random.randint(MIN, MAX, size = (length, width))

def verify(result: ndarray, check: ndarray) -> bool:
    """
    Checks if result is correct

    Args:
        result (ndarray): Calculated result
        check (ndarray): Numpy's result

    Returns:
        bool: True if correct, False otherwise
    """
    return array_equal(result, check)

def print_outcome(result: ndarray, check: ndarray) -> None:
    """
    Prints calculation's outcome (i.e. correctness)

    Args:
        result (ndarray): Calculated result
        check (ndarray): Numpy's result
    """
    if verify(result, check):
        print("\nCORRECT CALCULATION!")
        exit(1)

    else:
        print("\nINCORRECT CALCULATION...")
        exit(0)

def combine_results(matrix_products: dict) -> ndarray:
    """
    Combines all separate submatrices into a single matrix

    Args:
        matrix_products (dict): Dictionary to store results (i.e. Value = Chunk of Matrix A * Chunk of Matrix B at Key = given position)

    Returns:
        ndarray: Combined result of given matrices
    """
    # Declare list for storing combined results, and end index
    combined_results, end = [], 0

    # Get all results from the queue, sorted by its position
    results = [value for _, value in sorted(matrix_products.items())]

    # Sum all values in the same row, then add to combined_results
    for i in range(0, len(results), VERTICAL_PARTITIONS):
        end += VERTICAL_PARTITIONS
        combined_results.append(sum(results[i:end]))

    # Combine all results into a single matrix
    return concatenate(combined_results)
