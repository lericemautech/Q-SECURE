from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, error
from pickle import loads, dumps
from numpy import dot, ndarray
from Client import BUFFER, PORTS, HOST, TIMEOUT, HEADERSIZE

class Server:
    def __init__(self, port: int, host: str = HOST):
        # Server's port
        self._port: int = port

        # Server's IP Address
        self._host: str = host

    def multiply_matrix(self, matrix_a: ndarray, matrix_b: ndarray, index: int) -> tuple[ndarray, int]:
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
            data, new_data, msg_length = b"", True, 0
            
            # Receive data from client
            while True:
                packet = client_socket.recv(BUFFER)
                if not packet:
                    break
                data += packet

                # Check if entire message has been received
                if new_data:
                    msg_length = int(data[:HEADERSIZE])
                    new_data = False

                if len(data) - HEADERSIZE >= msg_length:
                    break

            # Unpack data (i.e. partitions of Matrix A and Matrix B and their position)
            matrix_a_partition, matrix_b_partition, index = loads(data[HEADERSIZE:HEADERSIZE + msg_length]) #loads(data)
            print(f"Received [{index}]: {matrix_a_partition} and {matrix_b_partition}")

            # Send acknowledgment to client
            ack_msg = "ACK"
            ack_msg = bytes(f"{len(ack_msg):<{HEADERSIZE}}", "utf-8") + ack_msg.encode("utf-8")
            client_socket.sendall(ack_msg)

            # Multiply partitions of Matrix A and Matrix B, while keeping track of their position
            result = Server.multiply_matrix(self, matrix_a_partition, matrix_b_partition, index)
            
            # Convert results to bytes
            result_data = dumps(result)

            # Add header to results packet
            result_data = bytes(f"{len(result_data):<{HEADERSIZE}}", "utf-8") + result_data

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
                server_socket.settimeout(TIMEOUT)

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

                    # Handle client (i.e. get position and partitions of Matrix A and Matrix B, multiply them, then send result and its position back to client)
                    Server.handle_client(self, client_socket)

        # Catch exception
        except error as msg:
            print(f"ERROR: {msg}")

if __name__ == "__main__":
    # Create server at 1st port in PORTS list
    server = Server(port = PORTS[0])

    # Start server
    server.start_server()