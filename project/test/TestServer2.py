from project.src.Server import SERVER_LOGGER, Server as Server
from project.src.Client import ADDRESSES

if __name__ == "__main__":
    SERVER_LOGGER.info("Initializing Server 2...")
    # Create server at 2nd Address
    server = Server(ADDRESSES[1])

    # Start server
    SERVER_LOGGER.info("Starting Server 2...")
    server.start_server()