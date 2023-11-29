from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, error
from pickle import loads, dumps
from numpy import dot, ndarray
from platform import platform, processor
from Shared import receive_data, send_data

class Server():
    def __init__(self, address: tuple[str, int]):
        # Server's IP Address and port
        self._address = address

        # Information about server (i.e. CPU model and OS)
        self._information: dict = { "PORT" : self._address[1], "CPU" : processor(), "OS" : platform() }

        # Server's network card
        #self._network_card: list[tuple[int, str]] = if_nameindex()        

    def multiply_matrices(self, matrix_a: ndarray, matrix_b: ndarray, index: int) -> tuple[ndarray, int]:
        """
        Multiply 2 matrices

        Args:
            matrix_a (ndarray): Matrix A
            matrix_b (ndarray): Matrix B
            index (int): Matrix position

        Returns:
            tuple[ndarray, int]: Multiple of Matrix A and Matrix B, its position
        """
        return dot(matrix_a, matrix_b), index

    def send(self, client_socket: socket, data: bytes) -> None:
        """
        Send data to client

        Args:
            client_socket (socket): Client socket
            data (bytes): _description_
        """
        # Add header to and send acknowledgment packet
        send_data(client_socket, "ACK".encode("utf-8"))
        
        # Add header to and send message packet back to client
        send_data(client_socket, data)

    def handle_client(self, client_socket: socket) -> None:
        """
        Get partitions of Matrix A and Matrix B from client, multiply them, then send result back to client

        Args:
            client_socket (socket): Client socket
        """
        try:            
            # Receive data from client
            data = receive_data(client_socket)

            if loads(data) == "INFO":
                print("Received request from client for server information")
                
                # Convert server information to bytes, then send to client
                Server.send(self, client_socket, dumps(self._information))
                print(f"\nSent: {self._information}\n")

            elif isinstance(loads(data), tuple):
                # Unpack data (i.e. partitions of Matrix A and Matrix B and their position)
                matrix_a_partition, matrix_b_partition, index = loads(data)
                print(f"Received [{index}]: {matrix_a_partition} and {matrix_b_partition}")

                # Multiply partitions of Matrix A and Matrix B, while keeping track of their position
                result = Server.multiply_matrices(self, matrix_a_partition, matrix_b_partition, index)
            
                # Convert result to bytes, then send back to client
                Server.send(self, client_socket, dumps(result))
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

                # Set socket's timeout
                #server_socket.settimeout(TIMEOUT)

                # Bind socket to server's address
                server_socket.bind(self._address)

                # Listen for connection(s)
                server_socket.listen()
                print(f"Server listening at {self._address}...")

                while True:
                    # Accept connection from client
                    client_socket, client_address = server_socket.accept()
                    print(f"Accepted connection from {client_address}\n")

                    # Handle client (i.e. get position and partitions of Matrix A and Matrix B,
                    # multiply them, then send result and its position back to client)
                    Server.handle_client(self, client_socket)

        # Catch exception
        except error as msg:
            print(f"ERROR: {msg}")
            exit(1)

        # Exit gracefully
        finally:
            exit(0)

    @property
    def information(self) -> dict:
        """
        Get server information (i.e. port, CPU model and OS)

        Returns:
            dict[int, str, str]: Server's port, CPU model, and OS
        """
        return self._information