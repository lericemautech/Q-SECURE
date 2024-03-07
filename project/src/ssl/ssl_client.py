from socket import socket, AF_INET, SOCK_STREAM
from ssl import TLSVersion, create_default_context, Purpose
from project.src.Shared import send, TLS_LOG, SERVER_ADDRESSES, CERTIFICATE_AUTHORITY, CLIENT_CERT, CLIENT_KEY

class SSLClient:
    def __init__(
        self, server_host, server_port
    ):
        self.server_host = server_host
        self.server_port = server_port
        self._context = create_default_context(Purpose.SERVER_AUTH, cafile = CERTIFICATE_AUTHORITY)
        self._context.load_cert_chain(CLIENT_CERT, CLIENT_KEY)
        self._context.check_hostname = True
        self._context.minimum_version = TLSVersion.TLSv1_3 # Latest version of TLS
        self._context.keylog_filename = TLS_LOG

    def connect(self):
        with self._context.wrap_socket(socket(AF_INET, SOCK_STREAM), server_hostname=self.server_host) as sock:
            sock.connect(SERVER_ADDRESSES[0])#(self.server_host, self.server_port))
            send(sock, b"Hello, server! This was encrypted.")

# openssl req -newkey rsa:2048 -x509 -sha256 -nodes -out device.csr -keyout device.key -addext "subjectAltName=DNS:127.0.0.1" -subj "/O=ACyD Lab/CN=127.0.0.1"

# socks = [ socket.socket(socket.AF_INET, socket.SOCK_STREAM) ] * NUM_SERVERS
# for sock in socks:
#     sock.connect((TCP_IP, TCP_PORT))
#     #sock.send(MESSAGE.encode())
#     TCP_PORT += 1

# msgs = [ "hi", "hello", "hey" ]
# #i = 0

# for m in msgs:
#     #sock = socks[i % NUM_SERVERS]
#     for sock in socks:
#         print("<Client>Sending: " + m + " to " + str(sock.getsockname()))
#         sock.send(m.encode())

#     for sock in socks:
#         data = sock.recv(BUFFER_SIZE)
#         print("Received: " + data.decode() + " from " + str(sock.getsockname()))
#         if not data:
#             print('\n<Client>Disconnected from server', str(sock.getsockname()))
#             sock.close()

    #i += 1
# s = socket(AF_INET, SOCK_STREAM)
# s.connect((TCP_IP, TCP_PORT))
# s.send(MESSAGE.encode())
# socket_list = [s] # socks
# i = 0

# if __name__ == "__main__":
#     # Create a context, just like as for the server
#     context = SSLContext() #create_default_context()
#     # Load the server's CA
#     context.load_verify_locations(f"{getcwd()}/project/file/keys/rootCA.pem")
    
#     # Wrap the socket, just as like in the server.
#     with socket(AF_INET, SOCK_STREAM) as sock, context.wrap_socket(sock, server_side=False, server_hostname=TCP_IP) as ssock:
#         ssock.connect((TCP_IP, TCP_PORT))
#         ssock.sendall(b"Hello, server! This was encrypted.")
#         print(ssock.getpeercert(True))
    
    # Connect and send data! Standard python socket stuff can go here.
# while True:
#     read_sockets, write_sockets, error_sockets = select(socket_list, [], [])

#     for sock in read_sockets:
#         # incoming message from remote server
#         if sock == s:
#             data = sock.recv(BUFFER_SIZE)
#             if not data:
#                 print('\nDisconnected from server')
#                 s.close()

#             else:
#                 print(f"\n{data.decode()}")
#                 #sys.stdout.flush()

#         else:
#             msg = f"some msg {i}"#sys.stdin.readline()
#             s.send(msg.encode())
#             #sys.stdout.flush()
#             i += 1