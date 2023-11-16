from socket import socket, AF_INET, SOCK_STREAM
from pickle import loads, dumps
from numpy import ndarray, random

# get small matrix client
# call func to partition in main

HOST = "127.0.0.1"
PORT = 12345
TIMEOUT = 5
BUFFER = 4096
LENGTH = 2

def send_matrices(server_address: tuple, matrix_a: ndarray, matrix_b: ndarray) -> ndarray:
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect(server_address)

    matrices = {'matrix_a': matrix_a, 'matrix_b': matrix_b}
    client_socket.send(dumps(matrices))

    data = client_socket.recv(BUFFER)
    result_matrix = loads(data)

    client_socket.close()
    return result_matrix

if __name__ == "__main__":
    # Example matrices for testing
    matrix_a = random.rand(LENGTH, LENGTH)
    matrix_b = random.rand(LENGTH, LENGTH)

    server_address = (HOST, PORT)
    result = send_matrices(server_address, matrix_a, matrix_b)

    print("Matrix A:")
    print(matrix_a)
    print("\nMatrix B:")
    print(matrix_b)
    print("\nResult Matrix:")
    print(result)