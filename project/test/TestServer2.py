from project.src.Server import Server as Server
from project.src.Client import SERVER_ADDRESSES

if __name__ == "__main__":
    # Create server at 2nd Address
    server = Server(SERVER_ADDRESSES[1])

    # Start server
    server.start_server()