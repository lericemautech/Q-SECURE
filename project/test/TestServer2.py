from project.src.Server import Server as Server
from project.src.Client import ADDRESSES

if __name__ == "__main__":
    # Create server at 2nd Address
    server = Server(ADDRESSES[1])

    # Start server
    server.start_server()