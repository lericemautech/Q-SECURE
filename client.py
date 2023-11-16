# matrix_client.py
import socket
import pickle
import numpy as np

def send_matrices(server_address, matrix_a, matrix_b):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(server_address)

    matrices = {'matrix_a': matrix_a, 'matrix_b': matrix_b}
    client_socket.send(pickle.dumps(matrices))

    data = client_socket.recv(4096)
    result_matrix = pickle.loads(data)

    client_socket.close()
    return result_matrix

if __name__ == "__main__":
    # Example matrices for testing
    matrix_a = np.random.rand(2, 2)
    matrix_b = np.random.rand(2, 2)

    server_address = ('127.0.0.1', 12345)
    result = send_matrices(server_address, matrix_a, matrix_b)

    print("Matrix A:")
    print(matrix_a)
    print("\nMatrix B:")
    print(matrix_b)
    print("\nResult Matrix:")
    print(result)