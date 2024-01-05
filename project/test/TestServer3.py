from project.src.Server import SERVER_LOGGER, Server as Server
from project.src.Client import ADDRESSES

if __name__ == "__main__":
    SERVER_LOGGER.info("Initializing Server 3...")
    # Create server at 3rd Address
    server = Server(ADDRESSES[2])

    # Start server
    SERVER_LOGGER.info("Starting Server 3...")
    server.start_server()