from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, error
from pickle import loads, dumps
from numpy import ndarray, dot
from typing import NamedTuple
from Shared import Address, receive, send

class Matrix(NamedTuple):
    matrix: ndarray
    index: int

class Server():
    def __init__(self, address: Address):
        # Server's IP Address and port
        self._server_address = address

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

        # Catch exception
        except error as msg:
            print(f"ERROR: {msg}")

        # Close client socket once done
        finally:
            client_socket.close()

    def start_server(self) -> None:
        """
        Start server and listen for connections
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

        # Catch exception
        except error as msg:
            print(f"ERROR: {msg}")
            exit(1)

        # Exit gracefully
        finally:
            exit(0)