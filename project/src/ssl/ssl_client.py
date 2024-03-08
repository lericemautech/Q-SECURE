from socket import socket
from ssl import Purpose, TLSVersion, VERIFY_X509_STRICT, create_default_context
from project.src.ssl.ssl_shared import TLS_LOG, CERTIFICATE_AUTHORITY, CLIENT_CERT, CLIENT_KEY
from project.src.Shared import SERVER_ADDRESSES, send

class SSLClient:
    def __init__(self, address):
        self.server_host = address.ip
        self.server_port = address.port
        self._context = create_default_context(Purpose.SERVER_AUTH, cafile = CERTIFICATE_AUTHORITY)
        self._context.load_cert_chain(CLIENT_CERT, CLIENT_KEY)
        self._context.minimum_version = TLSVersion.TLSv1_3 # Latest version of TLS
        self._context.keylog_filename = TLS_LOG
        self._context.verify_flags = VERIFY_X509_STRICT
        self._context.set_ciphers("HIGH:RSA")
        
    def connect(self):
        with self._context.wrap_socket(socket(), server_hostname = self.server_host) as sock:
            sock.connect((self.server_host, self.server_port))
            send(sock, b"Hello, server! This was encrypted.")

# TODO certificate bundle?
if __name__ == "__main__":
    c = SSLClient(SERVER_ADDRESSES[0])
    c.connect()