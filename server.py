import socket

HOST = socket.gethostname() # Raspberry Pi's IP address
PORT = 12345
TIMEOUT = 30

def send(sock, msg):
    sock.send(msg.encode())

def receive(sock, msg):
    pass

def connect():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.settimeout(TIMEOUT)
            sock.bind((HOST, PORT))
            sock.listen(TIMEOUT)

        except socket.error as msg:
            sock.close()
            print("ERROR: %s\n" % msg)
            exit(1)

        while True:
            print("Connecting...")
            
            try:
                # Accept client connection
                connection, address = sock.accept()
                print("Got connection from", address)

                # Send a message to client
                connection.send("Thank you for connecting".encode())

                # Close the connection
                connection.close()
                
            except socket.error as msg:
                sock.close()
                print("ERROR: %s\n" % msg)
                exit(1)

            finally:
                sock.close()

if __name__ == "__main__":
    print("Starting server...")