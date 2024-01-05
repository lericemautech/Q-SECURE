from project.src.Server import SERVER_LOGGER, Server as Server
from project.src.Client import ADDRESSES

if __name__ == "__main__":
    SERVER_LOGGER.info("Initializing Server 1...")
    # Create server at 1st Address
    server = Server(ADDRESSES[0])

    # Start server
    SERVER_LOGGER.info("Starting Server 1...")
    server.start_server()