from project.src.Server import Server as Server
from project.src.Client import ADDRESSES

if __name__ == "__main__":
    # Create server at 3rd port in PORTS list
    server = Server(ADDRESSES[2])

    # Start server
    server.start_server()