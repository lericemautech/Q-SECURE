from Server import Server, PORTS

if __name__ == "__main__":
    # Create server at 2nd port in PORTS list
    server = Server(port = PORTS[1])

    # Start server
    server.start_server()