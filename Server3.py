from Server import Server
from Client import ADDRESSES

if __name__ == "__main__":
    # Create server at 3rd port in PORTS list
    server = Server(ADDRESSES[2])

    # Start server
    server.start_server()