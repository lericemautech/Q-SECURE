from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, error
from pickle import loads, dumps
from numpy import dot, ndarray
from Client import BUFFER, PORTS, HOST, TIMEOUT

class Server:
    def __init__(self, port: int, host: str = HOST, timeout: int = TIMEOUT):
        self._port: int = port
        self._host: str = host
        self._timeout: int = timeout

    def multiply_matrix(self, matrix_a: ndarray, matrix_b: ndarray, index: int) -> tuple[ndarray, int]:
        """
        Multiply 2 matrices

        Args:
            matrix_a (ndarray): Matrix A
            matrix_b (ndarray): Matrix B
            index (int): Matrix position

        Returns:
            tuple: Multiple of Matrix A and Matrix B, its position
        """
        return dot(matrix_a, matrix_b), index

    def handle_client(self, client_socket: socket) -> None:
        """
        Get partitions of Matrix A and Matrix B from client, multiply them, then send result back to client

        Args:
            client_socket (socket): Client socket
        """
        try:
            data = client_socket.recv(BUFFER)
            matrix_a_partition, matrix_b_partition, index = loads(data)
            print(f"Received [{index}]: {matrix_a_partition} and {matrix_b_partition} at {client_socket.getsockname()}")
            results = Server.multiply_matrix(self, matrix_a_partition, matrix_b_partition, index)
            print(f"These are the results: {results}\n")
            client_socket.sendall(dumps(results))

        except error as msg:
            print("ERROR: %s\n" % msg)

        finally:
            client_socket.close()

    def start_server(self) -> None:
        """
        Start server and listen for connections
        """
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        
        try:
            server_socket.settimeout(TIMEOUT)
            server_socket.bind((self._host, self._port))
            server_socket.listen(1)
            print(f"Server listening on Port {self._port}...")

            while True:
                client_socket, addr = server_socket.accept()
                print(f"Accepted connection from {addr}\n")
                Server.handle_client(self, client_socket)

        except error as msg:
            print("ERROR: %s\n" % msg)

        except KeyboardInterrupt:
            print("ERROR: Keyboard Interrupted!\n")

        finally:
            server_socket.close()

if __name__ == "__main__":
    server = Server(port = PORTS[0])
    server.start_server()