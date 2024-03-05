from socket import socket, AF_INET, SOCK_STREAM
from ssl import SSLContext, OP_NO_TLSv1, OP_NO_TLSv1_1, OP_NO_TLSv1_2, OP_NO_SSLv2, OP_NO_SSLv3

class SSLClient:
    def __init__(
        self, server_host, server_port, client_cert, client_key,
    ):
        self.server_host = server_host
        self.server_port = server_port
        self._context = SSLContext()
        # only use TLSv1.3 (latest version of TLS at the moment)
        self._context.options |= OP_NO_TLSv1 | OP_NO_TLSv1_1 | OP_NO_TLSv1_2 | OP_NO_SSLv2 | OP_NO_SSLv3
        self._context.load_cert_chain(client_cert, client_key)

    def connect(self):
        with self._context.wrap_socket(socket(AF_INET, SOCK_STREAM)) as sock:
            sock.connect((self.server_host, self.server_port))
            sock.send(b"Hello, world!")