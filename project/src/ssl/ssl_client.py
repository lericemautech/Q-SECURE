from socket import socket, AF_INET, SOCK_STREAM
from ssl import SSLContext

class SSLClient:
    def __init__(
        self, server_host, server_port, server_sni_hostname, client_cert, client_key,
    ):
        self.server_host = server_host
        self.server_port = server_port
        self.server_sni_hostname = server_sni_hostname
        self._context = SSLContext()
        self._context.load_cert_chain(client_cert, client_key)
        self._sock = None

    def __del__(self):
        self.close()

    def connect(self):
        self._sock = self._context.wrap_socket(socket(AF_INET, SOCK_STREAM),server_hostname=self.server_sni_hostname)
        self._sock.connect((self.server_host, self.server_port))

    def send(self, msg):
        self._sock.send(msg.encode()) # type: ignore

    def close(self):
        self._sock.close() # type: ignore