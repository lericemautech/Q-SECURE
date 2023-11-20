from socket import socket, AF_INET, SOCK_STREAM, error
from pickle import loads, dumps
from numpy import dot, ndarray

HOST = "127.0.0.1"
PORT = 12345
TIMEOUT = 5
BUFFER = 4096
VERTICAL_PARTITIONS = 2

def multiply_matrices(matrix_a: ndarray, matrix_b: ndarray) -> ndarray:
    """
    Multiply 2 matrices

    Args:
        matrix_a (ndarray): Matrix A
        matrix_b (ndarray): Matrix B

    Returns:
        ndarray: Multiple of Matrix A and Matrix B
    """
    return dot(matrix_a, matrix_b)

def handle_client(client_socket: socket) -> None:
    """
    Get partitions of Matrix A and Matrix B from client, multiply them, then send result back to client

    Args:
        client_socket (socket): Client socket
    """
    results = { }

    try:
        data = client_socket.recv(BUFFER)
        matrices = loads(data)
        matrix_a_partitions, matrix_b_partitions = matrices["matrix_a"], matrices["matrix_b"]
        for i in range(len(matrix_a_partitions)):
            results[i] = multiply_matrices(matrix_a_partitions[i], matrix_b_partitions[i % VERTICAL_PARTITIONS])
        print(f"These are the results: {results}\n")
        client_socket.send(dumps(results))
        client_socket.close()

    except error as msg:
        client_socket.close()
        print("ERROR: %s\n" % msg)
        exit(0)

def start_server() -> None:
    """
    Start server and listen for connections
    """
    server_socket = socket(AF_INET, SOCK_STREAM)
    try:
        server_socket.settimeout(TIMEOUT)
        server_socket.bind((HOST, PORT))
        server_socket.listen(TIMEOUT)
        print(f"Server listening on Port {PORT}...")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"Accepted connection from {addr}\n")
            handle_client(client_socket)

    except error as msg:
        server_socket.close()
        print("ERROR: %s\n" % msg)
        exit(0)

if __name__ == "__main__":
    start_server()