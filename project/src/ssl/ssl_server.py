from socket import socket, AF_INET, SOCK_STREAM
from ssl import create_default_context, Purpose, CERT_REQUIRED
from project.src.ssl.ssl_test import server_host, server_port, server_cert, server_key, client_cert

class SSLServer:
    def __init__(
        self, host, port, server_cert, server_key, client_cert
    ):
        self.host = host
        self.port = port
        self._context = create_default_context(Purpose.CLIENT_AUTH)
        self._context.verify_mode = CERT_REQUIRED
        self._context.load_cert_chain(server_cert, server_key)
        self._context.load_verify_locations(client_cert)

    def connect(self):
        with socket(AF_INET, SOCK_STREAM, 0) as sock:
            sock.bind((self.host, self.port))
            sock.listen(5)
            while True:
                conn, _ = sock.accept()
                with self._context.wrap_socket(conn, server_side=True) as sconn:
                    self._recv(sconn)

    def _recv(self, sock):
        buf = b""
        while True:
            data = sock.recv(4096)
            if data:
                buf += data
                print(buf.decode())
            else:
                print("Received", buf.decode())
                break
if __name__ == "__main__":
    s = SSLServer(server_host, server_port, server_cert, server_key, client_cert)
    s.connect()