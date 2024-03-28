from numpy import ndarray, dot
from logging import getLogger, Logger
from time import perf_counter
from typing import NamedTuple
from project.src.ExceptionHandler import handle_exceptions
from project.src.server.Shared import start_server, validate_input, get_address, document_info
from project.src.Shared import (Address, FILE_DIRECTORY_PATH,
                                create_logger, timing)

# TODO Threading
# TODO Fix logging for server(s)
# https://docs.python.org/2/howto/logging-cookbook.html#sending-and-receiving-logging-events-across-a-network

SERVER_LOGGER = getLogger(__name__)
"""Server logger"""

class Matrix(NamedTuple):
    """
    Tuple defining matrix and its position

    Args:
        NamedTuple (int, ndarray): Index and matrix
    """
    index: int
    matrix: ndarray

class OriginalServer():
    def __init__(self, directory_path: str = FILE_DIRECTORY_PATH):
        create_logger("server.log")
        SERVER_LOGGER.info("Starting Original Server...\n")
        
        # Encrypted Server's IP Address and port
        server_address: Address | None = get_address()

        # Ensure server address and directory path are valid
        validate_input(server_address, directory_path, SERVER_LOGGER)

        # Document server info
        document_info(server_address, SERVER_LOGGER)

        # Start server
        self._start_unencrypted_server(server_address, SERVER_LOGGER)

    @handle_exceptions(SERVER_LOGGER)
    def _start_unencrypted_server(self, server_address: Address, logger: Logger) -> None:
        """
        Start Original Server

        Args:
            server_address (Address): Server's address
            logger (Logger): Logger
        """
        start_server(self, server_address, logger)

    def _multiply(self, matrix_a: ndarray, matrix_b: ndarray, index: int) -> Matrix:
        """
        Multiply 2 matrices using multithreading

        Args:
            matrix_a (ndarray): Matrix A
            matrix_b (ndarray): Matrix B
            index (int): Matrix position

        Returns:
            Matrix: Position and multiple of Matrix A and Matrix B
        """
        start = perf_counter()

        # Multiply matrices
        product = Matrix(index, dot(matrix_a, matrix_b))

        end = perf_counter()
        SERVER_LOGGER.info(f"Multiplied matrices in {timing(end, start)} seconds\n")
        
        return product