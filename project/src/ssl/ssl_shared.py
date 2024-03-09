from os import path
from project.src.Shared import LOG_PATH, Address

KEYCHAIN_PATH = "/Users/kiran/.ssh/Certificates/Q-SECURE"
"""Parent Directory Path"""

CERTIFICATE_AUTHORITY = path.join(KEYCHAIN_PATH, "ca-cert.cer.pem")
CLIENT_CERT = path.join(KEYCHAIN_PATH, "client.cer.pem")
CLIENT_KEY = path.join(KEYCHAIN_PATH, "client.key.pem")
SERVER_CERT = path.join(KEYCHAIN_PATH, "server.cer.pem")
SERVER_KEY = path.join(KEYCHAIN_PATH, "server.key.pem")
TLS_LOG = path.join(LOG_PATH, "tls.log")
"""SSL/TLS Parameters"""

SERVER_ADDRESSES = [ Address("127.0.0.1", 12345), Address("127.0.0.1", 12346), Address("127.0.0.1", 12347) ]
#SERVER_ADDRESSES = [ Address("192.168.207.129", 12345), Address("192.168.207.130", 12346), Address("192.168.207.131", 12347) ]
"""Server Addresses"""