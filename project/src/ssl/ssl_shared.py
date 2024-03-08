from os import path
from project.src.Shared import LOG_PATH

KEYCHAIN_PATH = "/Users/kiran/.ssh/Certificates/Q-SECURE"
"""Parent Directory Path"""

CERTIFICATE_AUTHORITY = path.join(KEYCHAIN_PATH, "ca-cert.cer.pem")
CLIENT_CERT = path.join(KEYCHAIN_PATH, "client.cer.pem")
CLIENT_KEY = path.join(KEYCHAIN_PATH, "client.key.pem")
SERVER_CERT = path.join(KEYCHAIN_PATH, "server.cer.pem")
SERVER_KEY = path.join(KEYCHAIN_PATH, "server.key.pem")
TLS_LOG = path.join(LOG_PATH, "tls.log")
"""SSL/TLS Parameters"""