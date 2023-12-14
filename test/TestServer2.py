from src.Server import Server
from src.Client import ADDRESSES

if __name__ == "__main__":
    # Create server at 2nd port in PORTS list
    server = Server(ADDRESSES[1])

    # Start server
    server.start_server()