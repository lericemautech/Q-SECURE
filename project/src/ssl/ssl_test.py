from project.src.ssl import ssl_client as client
from project.src.Shared import CLIENT_CERT, CLIENT_KEY, SERVER_ADDRESSES

server_host = SERVER_ADDRESSES[0].ip
server_port = SERVER_ADDRESSES[0].port

# TODO certificate bundle
if __name__ == "__main__":    
    c = client.SSLClient(
        server_host, server_port, CLIENT_CERT, CLIENT_KEY
    )
    c.connect()