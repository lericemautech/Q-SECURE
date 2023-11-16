# matrix_server.py
from socket import socket, AF_INET, SOCK_STREAM
from pickle import loads, dumps
from numpy import dot, ndarray

HOST = "127.0.0.1"
PORT = 12345
TIMEOUT = 5
BUFFER = 4096

def multiply_matrices(matrix_a: ndarray, matrix_b: ndarray) -> ndarray:
    return dot(matrix_a, matrix_b)

def handle_client(client_socket: socket) -> None:
    data = client_socket.recv(BUFFER)
    matrices = loads(data)
    print('Receive matrix a:', matrices['matrix_a'])
    print('Receive matrix b:', matrices['matrix_b'])
    result_matrix = multiply_matrices(matrices['matrix_a'], matrices['matrix_b'])
    print('This is the result:', result_matrix)
    client_socket.send(dumps(result_matrix))
    client_socket.close()

def start_server() -> None:
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(TIMEOUT)
    print(f"Server listening on Port {PORT}...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")
        handle_client(client_socket)

if __name__ == "__main__":
    start_server()