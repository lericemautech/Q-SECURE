# matrix_client.py
import socket
import pickle
import numpy as np
from Shared import HEADERSIZE, BUFFER

HOSTS = ["192.168.186.128", "192.168.186.130"]
PORT = 9999
LENGTH = 32

def send_matrices(server_addresses, matrix_a, matrix_b):
    result_matrices = []

    # Calculate the number of servers and matrix block size
    num_servers = len(server_addresses)
    block_size = matrix_a.shape[0] // num_servers

    for i, server_address in enumerate(server_addresses):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            client_socket.connect(server_address)

            # Divide matrices and send to the server
            start_row = i * block_size
            end_row = start_row + block_size if i < num_servers - 1 else None

            submatrix_a = matrix_a[start_row:end_row, :]
            submatrix_b = matrix_b[:, start_row:end_row]

            matrices = {'matrix_a': submatrix_a, 'matrix_b': submatrix_b}
            dict_matrices = pickle.dumps(matrices)
            dict_matrices = bytes(f'{len(dict_matrices):<{HEADERSIZE}}', "utf-8") + dict_matrices
            client_socket.sendall(dict_matrices)

            # Receive acknowledgment from the server
            ack_data = client_socket.recv(HEADERSIZE)
            ack_msg_length = int(ack_data.decode("utf-8").strip())

            # Ensure the acknowledgment is "ACK"
            ack_msg = client_socket.recv(ack_msg_length).decode("utf-8").strip()
            if ack_msg != "ACK":
                raise ValueError(f"Invalid acknowledgment: {ack_msg}")

            # Receive the result matrix
            data = b""
            new_data = True
            msg_length = 0
            while True:
                packet = client_socket.recv(BUFFER)
                if not packet:
                    break
                data += packet

                # Check if the entire message has been received
                if new_data:
                    msg_length = int(data[:HEADERSIZE])
                    new_data = False

                if len(data) - HEADERSIZE >= msg_length:
                    break

            result_matrix = pickle.loads(data[HEADERSIZE:HEADERSIZE + msg_length])
            result_matrices.append(result_matrix)

        except Exception as e:
            print(f"Error connecting to {server_address}: {e}")
            result_matrices.append(None)

        finally:
            client_socket.close()

    return result_matrices

if __name__ == "__main__":
    # Example matrices for testing
    matrix_a = np.random.rand(LENGTH, LENGTH)
    matrix_b = np.random.rand(LENGTH, LENGTH)

    server_addresses = [(HOSTS[0], PORT), (HOSTS[1], PORT)]

    result_matrices = send_matrices(server_addresses, matrix_a, matrix_b)

    for i, result_matrix in enumerate(result_matrices):
        if result_matrix is not None:
            print(f"Result Matrix from Server {i + 1}:")
            print(result_matrix)
        else:
            print(f"Failed to receive result from Server {i + 1}.")