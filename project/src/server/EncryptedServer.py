from socket import socket, SOL_SOCKET, SO_REUSEADDR
from pickle import loads, dumps
from os import O_CREAT, O_WRONLY, path, cpu_count, umask, open as opener
from logging import getLogger, shutdown
from time import perf_counter
from psutil import virtual_memory
from platform import platform
from datetime import datetime
from sympy import Matrix
from project.src.ExceptionHandler import handle_exceptions
from project.src.Shared import (Address, ACKNOWLEDGEMENT, SERVER_INFO_PATH,
                                FILE_DIRECTORY_PATH, create_logger,
                                timing, receive, send)

# TODO Threading
# TODO Fix logging for server(s)
# https://docs.python.org/2/howto/logging-cookbook.html#sending-and-receiving-logging-events-across-a-network

SERVER_LOGGER = getLogger(__name__)
"""Server logger"""

class EncryptedServer():
    def __init__(self, directory_path: str = FILE_DIRECTORY_PATH):
        create_logger("server.log")
        SERVER_LOGGER.info("Starting Server...\n")
        
        # Server's IP Address and port
        server_address: Address | None = self._get_address()

        # Check if address is valid (i.e. has IP Address and port)
        if (server_address or server_address.ip or server_address.port) == None:
            exception_msg = f"Unable to determine server's IP Address"
            SERVER_LOGGER.exception(exception_msg)
            self._cleanup()
            raise ValueError(exception_msg)

        # Check if directory_path exists
        if not path.exists(directory_path):
            exception_msg = f"{directory_path} does not exist"
            SERVER_LOGGER.exception(exception_msg)
            self._cleanup()
            raise IOError(exception_msg)

        # Check if directory_path is actually a directory
        if not path.isdir(directory_path):
            exception_msg = f"{directory_path} is not a directory"
            SERVER_LOGGER.exception(exception_msg)
            self._cleanup()
            raise NotADirectoryError(exception_msg)

        # Document server info
        self._document_info(server_address)

        # Start server
        self._start_server(server_address)

    def _get_address(self) -> Address:
        """
        Get server's IP Address and port

        Returns:
            Address: Server's address
        """
        with socket() as sock:
            # Bind to open port
            sock.bind(("", 0))
            return Address(sock.getsockname()[0], sock.getsockname()[1])

    # TODO After x lines, create new file. After creating N files, delete N - 1 files.
    def _document_info(self, address: Address, filepath: str = SERVER_INFO_PATH) -> None:
        """
        Document server's IP Address, port, number of cores, available RAM, OS, and timestamp to SERVER_INFO_PATH

        Args:
            address (Address): Server's address
            filepath (str, optional): Path of file to read from; defaults to SERVER_INFO_PATH
        """
        # Append to file if < 1 GB; creates it if it does not exist or is empty
        if not path.exists(filepath) or not path.isfile(filepath) or path.getsize(filepath) < 1000000000: mode = "a"

        # Else, overwrite file if size >= 1 GB
        else: mode = "w"

        # File will have no privileges initially revoked
        # TODO If statement
        umask(0)

        # Create and write permissions to file for all users
        descriptor = opener(filepath, flags = O_CREAT | O_WRONLY, mode = 0o777)
        
        # Create file and write Server's IP Address, port, number of cores, available RAM, OS, and timestamp to file
        with open(descriptor, mode) as file:
            file.write(f"{address.ip} {address.port} {cpu_count()} {virtual_memory().available / 1000000000:.2f} {platform(terse = True)} {datetime.now()}\n")

        SERVER_LOGGER.info(f"Recorded information and timestamp for server at {address}\n")

    def _multiply(self, matrix_a: Matrix, matrix_b: Matrix, index: int) -> tuple[int, Matrix]:
        """
        Multiply 2 matrices using multithreading

        Args:
            matrix_a (Matrix): Matrix A
            matrix_b (Matrix): Matrix B
            index (int): Matrix position

        Returns:
            tuple[int, Matrix]: Position and multiple of Matrix A and Matrix B
        """
        start = perf_counter()

        # Multiply matrices
        product = matrix_a.multiply(matrix_b)

        end = perf_counter()
        SERVER_LOGGER.info(f"Multiplied matrices in {timing(end, start)} seconds\n")
        
        return index, product
        
    def _send_client(self, client_socket: socket, data: bytes, server_address: Address) -> None:
        """
        Send data to client

        Args:
            client_socket (socket): Client socket
            data (bytes): Message packet (i.e. data) to send to client
            server_address (Address): Server address
        """
        start = perf_counter()
        
        # Add header to and send acknowledgment packet
        send(client_socket, ACKNOWLEDGEMENT.encode("utf-8"))

        # Add header to and send message packet back to client
        send(client_socket, data)

        end = perf_counter()
        SERVER_LOGGER.info(f"Server at {server_address} sent acknowledgement and message packet back to client {client_socket} in {timing(end, start)} seconds\n")

    def _handle_client(self, client_socket: socket, server_address: Address) -> None:
        """
        Get partitions of Matrix A and Matrix B from client, multiply them, then send result back to client

        Args:
            client_socket (socket): Client socket
            server_address (Address): Server address

        Raises:
            EOFError: Client is checking if server is listening
        """
        start = perf_counter()

        # Receive data from client
        data = receive(client_socket)

        # Unpack data (i.e. partitions of Matrix A and Matrix B and their position)
        try:
            matrix_a_partition, matrix_b_partition, index = loads(data)
            print(f"Received and unpacked [{index}]: {matrix_a_partition} and {matrix_b_partition}")

        # Catch error encountered when client is checking if server is listening
        except EOFError:
            SERVER_LOGGER.info(f"Client {client_socket} is checking if server at {server_address} is listening\n")
            return

        except:
            SERVER_LOGGER.exception(f"Unexpected error occurred... server at {server_address} will stop handling client {client_socket}\n")
            return

        # Multiply partitions of Matrix A and Matrix B, while keeping track of their position
        result = self._multiply(matrix_a_partition, matrix_b_partition, index)
        
        # Convert result to bytes, then send back to client
        self._send_client(client_socket, dumps(result), server_address)
        print(f"\nSent: {result}\n")

        end = perf_counter()
        SERVER_LOGGER.info(f"Successfully handled client in {timing(end, start)} second(s)\n")

    def _cleanup(self) -> None:
        """
        Shutdown logger
        """
        SERVER_LOGGER.info("Shutting down logger...\n")
        shutdown()

    @handle_exceptions(SERVER_LOGGER)
    def _start_server(self, server_address: Address) -> None:
        """
        Start server and listen for connections
        
        Args:
            server_address (Address): Server address

        Raises:
            KeyboardInterrupt: Server disconnected due to keyboard (i.e. CTRL + C)
        """
        start = perf_counter()
        
        try:
            with socket() as server_socket:
                # Allow reuse of address
                server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

                # Bind socket to server's address
                server_socket.bind(server_address)

                # Listen for connection(s)
                server_socket.listen()
                listen_msg = f"Server at {server_address} listening for connection(s)..."
                SERVER_LOGGER.info(f"{listen_msg}\n")
                print(listen_msg)

                while True:
                    # Accept connection from client
                    client_socket, client_address = server_socket.accept()
                    SERVER_LOGGER.info(f"Server at {server_address} accepted connection from {client_address}\n")

                    # TODO Break out of while loop if client address is not an allowed address

                    # Handle client (i.e. get position and partitions of Matrix A and Matrix B,
                    # multiply them, then send result and its position back to client)
                    self._handle_client(client_socket, server_address)

        # Catch error encountered when server is disconnected via CTRL + C
        except KeyboardInterrupt:
            print(f"\nServer at {server_address} disconnected")
            exit(0)

        finally:
            end = perf_counter()
            SERVER_LOGGER.info(f"Server at {server_address} ran for {timing(end, start)} seconds")
            self._cleanup()