from project.src.ssl import ssl_client as client
from os import path

server_host = "127.0.0.1"
server_port = 12345
keys_dir = "/Users/kiran/Documents/workspace/Projects/Q-SECURE/project/file/keys"
client_cert = path.join(keys_dir, "client.crt")
client_key = path.join(keys_dir, "client.key")
server_cert = path.join(keys_dir, "server.crt")
server_key = path.join(keys_dir, "server.key")

# TODO certificate bundle
if __name__ == "__main__":    
    c = client.SSLClient(
        server_host, server_port, client_cert, client_key
    )
    c.connect()