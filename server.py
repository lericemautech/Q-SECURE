# matrix_server.py
import socket
import pickle
import numpy as np

def multiply_matrices(matrix_a, matrix_b):
    return np.dot(matrix_a, matrix_b)

def handle_client(client_socket):
    data = client_socket.recv(4096)
    matrices = pickle.loads(data)
    print('Receive matrix a:', matrices['matrix_a'])
    print('Receive matrix b:', matrices['matrix_b'])
    result_matrix = multiply_matrices(matrices['matrix_a'], matrices['matrix_b'])
    print('This is the result:', result_matrix)
    client_socket.send(pickle.dumps(result_matrix))
    client_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', 12345))
    server_socket.listen(5)
    print("Server listening on port 12345...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")
        handle_client(client_socket)

if __name__ == "__main__":
    start_server()