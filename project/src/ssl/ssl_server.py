from socket import socket, AF_INET, SOCK_STREAM
from ssl import create_default_context, Purpose, CERT_REQUIRED, TLSVersion
from project.src.Shared import CLIENT_CERT, SERVER_CERT, SERVER_KEY, receive
from project.src.ssl.ssl_test import server_host, server_port

class SSLServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self._context = create_default_context(Purpose.CLIENT_AUTH)
        self._context.minimum_version = TLSVersion.TLSv1_3
        self._context.verify_mode = CERT_REQUIRED
        self._context.load_cert_chain(SERVER_CERT, SERVER_KEY)
        self._context.load_verify_locations(CLIENT_CERT)

    def connect(self):
        with socket(AF_INET, SOCK_STREAM, 0) as sock:
            sock.bind((self.host, self.port))
            sock.listen(5)
            while True:
                conn, _ = sock.accept()
                with self._context.wrap_socket(conn, server_side=True) as sconn:
                    print("Received", receive(sconn).decode())

if __name__ == "__main__":
    s = SSLServer(server_host, server_port)
    s.connect()