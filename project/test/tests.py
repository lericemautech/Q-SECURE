import socket, select
from threading import Thread

TCP_IP = "127.0.0.1"
TCP_PORT = 12345
BUFFER_SIZE = 4096

class ClientThread(Thread):
    def __init__(self,ip,port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        print("[+] New thread started for "+ip+":"+str(port))

    def run(self):
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data: break
            print("received data:", data)
            conn.send(b"<Server> Got your data. Send some more\n")

threads = []

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((TCP_IP, TCP_PORT))
server_socket.listen(10)

read_sockets, write_sockets, error_sockets = select.select([server_socket], [], [])

while True:
    print("Waiting for incoming connections...")
    for sock in read_sockets:
        (conn, (ip,port)) = server_socket.accept()
        newthread = ClientThread(ip,port)
        newthread.start()
        threads.append(newthread)

    for t in threads:
        t.join()