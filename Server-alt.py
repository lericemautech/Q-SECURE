# matrix_server.py
import socket
import pickle

HOSTS = ["192.168.186.128", "192.168.186.130"]
PORT = 9999
BUFFER = 4096
HEADERSIZE = 10

def handle_client(client_socket):
    # Receive matrices
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

    matrices = pickle.loads(data[HEADERSIZE:HEADERSIZE + msg_length])
    matrix_a = matrices['matrix_a']
    matrix_b = matrices['matrix_b']

    # Send acknowledgment to the client
    ack_msg = "ACK"
    ack_msg = bytes(f'{len(ack_msg):<{HEADERSIZE}}', "utf-8") + ack_msg.encode("utf-8")
    client_socket.sendall(ack_msg)

    # Perform matrix multiplication for each block
    result_matrices = []
    for i in range(0, matrix_a.shape[0], block_size):
        block_a = matrix_a[i:i + block_size, :]
        block_b = matrix_b[:, i:i + block_size]

        result_block = block_a @ block_b  # Example matrix multiplication, adjust as needed
        result_matrices.append(result_block)

        # Send the result back to the client
        result_data = pickle.dumps({'result_block': result_block})
        result_data = bytes(f'{len(result_data):<{HEADERSIZE}}', "utf-8") + result_data
        client_socket.sendall(result_data)

    client_socket.close()

if __name__ == "__main__":
    server_address = (HOSTS[1], PORT)
    block_size = 8

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(server_address)
    server_socket.listen(5)

    print(f"Server listening on {server_address}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")

        handle_client(client_socket)