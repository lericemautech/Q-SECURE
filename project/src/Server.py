from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, error
from pickle import loads, dumps
from numpy import ndarray, dot
from typing import NamedTuple
from os import cpu_count, getcwd, path, rename
from platform import platform
from project.src.Shared import Address, receive, send

class Matrix(NamedTuple):
    matrix: ndarray
    index: int

class Server():
    def __init__(self, address: Address, directory_path: str = path.join(getcwd(), "project", "file")):
        # Server's IP Address and port
        self._server_address = address

        # Check if directory_path exists
        if not path.exists(directory_path):
            raise IOError(f"{directory_path} does not exist")

        # Check if directory_path is actually a directory
        if not path.isdir(directory_path):
            raise NotADirectoryError(f"{directory_path} is not a directory")

        # Write Server's IP Address, port, number of cores, and OS to file in directory_path
        self._document_info(directory_path)

    def _document_info(self, directory_path: str, remove_duplicates: bool = False) -> None:
        """
        Document server's IP Address, port, number of cores, and OS to "server_info.txt" at directory_path

        Args:
            directory_path (str): Path of the directory to write the file to
            remove_duplicates (bool, optional): Whether to remove entries with the same IP address
            and port as current Server. Defaults to False.
        """
        # Get current Server's IP Address and port
        ip, port = self._server_address.ip, self._server_address.port

        # Path of file to write to
        filepath = path.join(directory_path, "server_info.txt")

        # Removes entries with the same IP Address and port as current Server
        if remove_duplicates:
            # Path of temporary file to write to
            temp_filepath = path.join(directory_path, "temp_server_info.txt")

            # Read from original filepath and write to temporary filepath
            with open(filepath, "r") as in_file, open(temp_filepath, "w+") as out_file:
                for line in in_file:
                    # Get IP Address and port at current line
                    curr_ip, curr_port = line.split(" ")[:2]

                    # Write line to temp_server_info.txt if IP Address and port are not the same as current Server
                    if curr_ip != ip and curr_port != port:
                        out_file.write(line)

            # Rename temporary filepath to original filepath
            rename(temp_filepath, filepath)

        # Append (i.e. write at end) Server's IP Address, port, number of cores, and OS to file
        with open(filepath, "a") as file:
            file.write(f"{ip} {port} {cpu_count()} {platform(terse = True)}\n")

    def _multiply(self, matrix_a: ndarray, matrix_b: ndarray, index: int) -> Matrix:
        """
        Multiply 2 matrices

        Args:
            matrix_a (ndarray): Matrix A
            matrix_b (ndarray): Matrix B
            index (int): Matrix position

        Returns:
            Matrix: Multiple of Matrix A and Matrix B, its position
        """
        return Matrix(dot(matrix_a, matrix_b), index)
        
    def _send_client(self, client_socket: socket, data: bytes) -> None:
        """
        Send data to client

        Args:
            client_socket (socket): Client socket
            data (bytes): Message packet (i.e. data) to send to client
        """
        # Add header to and send acknowledgment packet
        send(client_socket, "ACK".encode("utf-8"))
        
        # Add header to and send message packet back to client
        send(client_socket, data)

    def _handle_client(self, client_socket: socket) -> None:
        """
        Get partitions of Matrix A and Matrix B from client, multiply them, then send result back to client

        Args:
            client_socket (socket): Client socket

        Raises:
            ConnectionRefusedError: Connection to client refused
            ConnectionError: Connection to client lost
        """
        try:
            # Receive data from client
            data = receive(client_socket)

            # Unpack data (i.e. partitions of Matrix A and Matrix B and their position)
            matrix_a_partition, matrix_b_partition, index = loads(data)
            print(f"Received [{index}]: {matrix_a_partition} and {matrix_b_partition}")

            # Multiply partitions of Matrix A and Matrix B, while keeping track of their position
            result = self._multiply(matrix_a_partition, matrix_b_partition, index)
        
            # Convert result to bytes, then send back to client
            self._send_client(client_socket, dumps(result))
            print(f"\nSent: {result}\n")

        except ConnectionRefusedError:
            raise ConnectionRefusedError(f"(Server._handle_client) Connection to client {client_socket} refused")
            
        except ConnectionError:
            raise ConnectionError(f"(Server._handle_client) Connection to client {client_socket} lost")
                
        except error as msg:
            print(f"ERROR: (Server._handle_client) {msg}")
            exit(1)

    def start_server(self) -> None:
        """
        Start server and listen for connections

        Raises:
            ConnectionRefusedError: Connection refused
            ConnectionError: Connection lost
        """
        try:
            with socket(AF_INET, SOCK_STREAM) as server_socket:
                # Allow reuse of address
                server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

                # Bind socket to server's address
                server_socket.bind(self._server_address)

                # Listen for connection(s)
                server_socket.listen()
                print(f"Server listening at {self._server_address}...")

                while True:
                    # Accept connection from client
                    client_socket, client_address = server_socket.accept()
                    print(f"Accepted connection from {client_address}\n")

                    # Handle client (i.e. get position and partitions of Matrix A and Matrix B,
                    # multiply them, then send result and its position back to client)
                    self._handle_client(client_socket)

        except ConnectionRefusedError:
            raise ConnectionRefusedError(f"(Server._start_server) Connection refused")
            
        except ConnectionError:
            raise ConnectionError(f"(Server._start_server) Connection lost")

        except error as msg:
            print(f"ERROR: (Server._start_server) {msg}")
            exit(1)