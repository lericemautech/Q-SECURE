from socket import socket
from ssl import VERIFY_X509_STRICT, create_default_context, Purpose, TLSVersion
from project.src.Shared import TLS_LOG, SERVER_ADDRESSES, CERTIFICATE_AUTHORITY, SERVER_CERT, SERVER_KEY, receive

class SSLServer:
    def __init__(self, address):
        self.host = address.ip
        self.port = address.port
        self._context = create_default_context(Purpose.CLIENT_AUTH, cafile = CERTIFICATE_AUTHORITY)
        self._context.load_cert_chain(SERVER_CERT, SERVER_KEY)
        self._context.minimum_version = TLSVersion.TLSv1_3 # Latest version of TLS
        self._context.keylog_filename = TLS_LOG
        self._context.verify_flags = VERIFY_X509_STRICT
        self._context.set_ciphers("HIGH:RSA")
        # TODO post_handshake_auth
        
    def connect(self):
        with socket() as sock:
            sock.bind((self.host, self.port))
            sock.listen(5)
            while True:
                conn, _ = sock.accept()
                print("Connected to:", conn.getpeername())
                with self._context.wrap_socket(conn, server_side = True) as wrapped_sock:
                    print("Received:", receive(wrapped_sock).decode())

if __name__ == "__main__":
    s = SSLServer(SERVER_ADDRESSES[0])
    s.connect()