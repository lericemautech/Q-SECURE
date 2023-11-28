from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, error
from pickle import loads, dumps
from numpy import dot, ndarray
from Shared import PORTS, HOST, TIMEOUT, receive_data, add_header

class Server():
    def __init__(self, port: int, host: str = HOST):
        # Server's port
        self._port: int = port

        # Server's IP Address
        self._host: str = host

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

    def handle_client(self, client_socket: socket) -> None:
        """
        Get partitions of Matrix A and Matrix B from client, multiply them, then send result back to client

        Args:
            client_socket (socket): Client socket
        """
        try:            
            # Receive data from client
            data = receive_data(client_socket)
            
            # Unpack data (i.e. partitions of Matrix A and Matrix B and their position)
            matrix_a_partition, matrix_b_partition, index = loads(data)
            print(f"Received [{index}]: {matrix_a_partition} and {matrix_b_partition}")

            # Add header to acknowledgment packet
            ack_msg = add_header("ACK".encode("utf-8"))
            
            # Send acknowledgment to client
            client_socket.sendall(ack_msg)

            # Multiply partitions of Matrix A and Matrix B, while keeping track of their position
            result = Server.multiply_matrices(self, matrix_a_partition, matrix_b_partition, index)
            
            # Convert result to bytes
            result_data = dumps(result)

            # Add header to results packet
            result_data = add_header(result_data)

            # Send results back to client
            client_socket.sendall(result_data)
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

                # Server's address
                server_address = (self._host, self._port)

                # Bind socket to server's address
                server_socket.bind(server_address)

                # Listen for connection(s)
                server_socket.listen()
                print(f"Server listening at {server_address}...")

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

if __name__ == "__main__":
    # Create server at 1st port in PORTS list
    server = Server(port = PORTS[0])

    # Start server
    server.start_server()