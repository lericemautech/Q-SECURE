from Server import Server, PORTS

if __name__ == "__main__":
    # Create server at 3rd port in PORTS list
    server = Server(port = PORTS[2])

    # Start server
    server.start_server()