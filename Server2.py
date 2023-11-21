from Server import Server, PORTS

if __name__ == "__main__":
    server = Server(port = PORTS[1])
    server.start_server()