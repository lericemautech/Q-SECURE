from socket import socket, SOL_SOCKET, SO_REUSEADDR
from pickle import loads, dumps
from numpy import ndarray, dot
from os import path, cpu_count, umask, O_CREAT, O_WRONLY, open as opener
from logging import getLogger, shutdown
from threading import Thread
from time import perf_counter
from psutil import virtual_memory
from platform import platform
from typing import NamedTuple
from datetime import datetime
from project.src.ExceptionHandler import handle_exceptions
from project.src.Shared import (Address, ACKNOWLEDGEMENT, FILEPATH,
                                FILE_DIRECTORY_PATH, create_logger,
                                timing, receive, send)

# TODO Fix logging for server(s)
# https://docs.python.org/2/howto/logging-cookbook.html#sending-and-receiving-logging-events-across-a-network

SERVER_LOGGER = getLogger(__name__)

class Matrix(NamedTuple):
    """
    Tuple defining matrix and its position

    Args:
        NamedTuple (int, ndarray): Index and matrix
    """
    index: int
    matrix: ndarray

# TODO Finish writing this class
class ClientThread(Thread):
    def __init__(self, address: Address):
        Thread.__init__(self)
        self.address = address
        SERVER_LOGGER.info(f"[+] New thread started for {address}\n")

    def run(self):
        while True:
            # data = recv(BUFFER)
            # if not data: break
            print("received data:")
            # conn.send(b"<Server> Got your data. Send some more\n")

class Server():
    def __init__(self, address: Address, directory_path: str = FILE_DIRECTORY_PATH):
        # Logging
        create_logger("server.log")
        SERVER_LOGGER.info("Starting Server...\n")
        
        # Check if address is valid (i.e. has IP Address and port)
        if not all(address):
            exception_msg = f"{address} does not have a valid IP Address and/or port"
            SERVER_LOGGER.exception(exception_msg)
            shutdown()
            raise ValueError(exception_msg)

        # Server's IP Address and port
        self._server_address = address

        # Check if directory_path exists
        if not path.exists(directory_path):
            exception_msg = f"{directory_path} does not exist"
            SERVER_LOGGER.exception(exception_msg)
            shutdown()
            raise IOError(exception_msg)

        # Check if directory_path is actually a directory
        if not path.isdir(directory_path):
            exception_msg = f"{directory_path} is not a directory"
            SERVER_LOGGER.exception(exception_msg)
            shutdown()
            raise NotADirectoryError(exception_msg)

        # Write Server's IP Address, port, number of cores, available RAM, OS, and timestamp to FILEPATH
        self._document_info()

    # TODO Filesize threshold ~1GB
    # TODO After x lines, create new file. After creating N files, delete N - 1 files.
    def _document_info(self) -> None:
        """
        Document server's IP Address, port, number of cores, available RAM, OS, and timestamp to FILEPATH
        """
        # Get current Server's IP Address and port
        ip, port = self._server_address.ip, self._server_address.port

        umask(0)
        descriptor = opener(FILEPATH, flags = O_CREAT | O_WRONLY, mode = 0o777)
        
        # Create file and write Server's IP Address, port, number of cores, available RAM, OS, and timestamp to file
        with open(descriptor, "a") as file:
            file.write(f"{ip} {port} {cpu_count()} {virtual_memory().available / 1000000000:.2f} {platform(terse = True)} {datetime.now()}\n")
            SERVER_LOGGER.info(f"Recorded information and timestamp for server at {self._server_address}\n")

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
        product = Matrix(index, dot(matrix_a, matrix_b))
        end = perf_counter()
        SERVER_LOGGER.info(f"Multiplied matrices in {timing(end, start)} seconds\n")
        return product
        
    def _send_client(self, client_socket: socket, data: bytes) -> None:
        """
        Send data to client

        Args:
            client_socket (socket): Client socket
            data (bytes): Message packet (i.e. data) to send to client
        """
        start_ack = perf_counter()
        
        # Add header to and send acknowledgment packet
        send(client_socket, ACKNOWLEDGEMENT.encode("utf-8"))
        
        end_ack = perf_counter()
        SERVER_LOGGER.info(f"Server at {self._server_address} sent acknowledgement to client {client_socket} in {timing(end_ack, start_ack)} seconds\n")
        start_send = perf_counter()
        
        # Add header to and send message packet back to client
        send(client_socket, data)

        end_send = perf_counter()
        SERVER_LOGGER.info(f"Server at {self._server_address} sent message packet back to client {client_socket} in {timing(end_send, start_send)} seconds\n")

    def _handle_client(self, client_socket: socket) -> None:
        """
        Get partitions of Matrix A and Matrix B from client, multiply them, then send result back to client

        Args:
            client_socket (socket): Client socket

        Raises:
            EOFError: Client is checking if server is listening
        """
        # Start timer
        start = perf_counter()

        # Receive data from client
        data = receive(client_socket)
        
        try:
            # Unpack data (i.e. partitions of Matrix A and Matrix B and their position)
            matrix_a_partition, matrix_b_partition, index = loads(data)
            print(f"Received and unpacked [{index}]: {matrix_a_partition} and {matrix_b_partition}\n")

        except EOFError:
            SERVER_LOGGER.info(f"Client {client_socket} is checking if server at {self._server_address} is listening\n")
            return

        except:
            SERVER_LOGGER.exception(f"Unexpected error occurred... server at {self._server_address} will stop handling client {client_socket}\n")
            return

        # Multiply partitions of Matrix A and Matrix B, while keeping track of their position
        result = self._multiply(matrix_a_partition, matrix_b_partition, index)
        
        # Convert result to bytes, then send back to client
        self._send_client(client_socket, dumps(result))
        print(f"\nSent: {result}\n")

        # End timer
        end = perf_counter()

        # Log method's speed
        SERVER_LOGGER.info(f"Successfully handled client in {timing(end, start)} second(s)\n")

    @handle_exceptions(SERVER_LOGGER)
    def start_server(self) -> None:
        """
        Start server and listen for connections

        Raises:
            KeyboardInterrupt: Server disconnected due to keyboard (i.e. CTRL + C)
        """
        start = perf_counter()
        
        try:
            with socket() as server_socket:                
                # Allow reuse of address
                server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

                # Bind socket to server's address
                server_socket.bind(self._server_address)

                # Listen for connection(s)
                server_socket.listen()
                listen_msg = f"Server at {self._server_address} listening for connection(s)..."
                SERVER_LOGGER.info(f"{listen_msg}\n")
                print(listen_msg)

                while True:
                    # Accept connection from client
                    client_socket, client_address = server_socket.accept()
                    SERVER_LOGGER.info(f"Server at {self._server_address} accepted connection from {client_address}\n")

                    # TODO Break out of while loop if client address is not an allowed address

                    # Handle client (i.e. get position and partitions of Matrix A and Matrix B,
                    # multiply them, then send result and its position back to client)
                    self._handle_client(client_socket)

        except KeyboardInterrupt:
            print(f"\nServer at {self._server_address} disconnected")
            exit(0)

        finally:
            end = perf_counter()
            SERVER_LOGGER.info(f"Server at {self._server_address} ran for {timing(end, start)} seconds")
            shutdown()