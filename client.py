import socket

HOST = socket.gethostname() # Raspberry Pi's IP address
PORT = 12345

def send(sock, msg):
    sock.send(msg.encode())

def receive(socket, msg):
    pass

def connect():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((HOST, PORT))
            print(sock.recv(1024).decode())

        except socket.error as msg:
            sock.close()
            print("ERROR: %s\n" % msg)
            exit(1)

        finally:
            sock.close()

if __name__ == "__main__":
    print("Starting client...")