import socket, select, sys

TCP_IP = "127.0.0.1"
TCP_PORT = 12345
BUFFER_SIZE = 4096
MESSAGE = "Hello, Server. Are you ready?\n"
NUM_SERVERS = 1

# socks = [ socket.socket(socket.AF_INET, socket.SOCK_STREAM) ] * NUM_SERVERS
# for sock in socks:
#     sock.connect((TCP_IP, TCP_PORT))
#     #sock.send(MESSAGE.encode())
#     TCP_PORT += 1

# msgs = [ "hi", "hello", "hey" ]
# #i = 0

# for m in msgs:
#     #sock = socks[i % NUM_SERVERS]
#     for sock in socks:
#         print("<Client>Sending: " + m + " to " + str(sock.getsockname()))
#         sock.send(m.encode())

#     for sock in socks:
#         data = sock.recv(BUFFER_SIZE)
#         print("Received: " + data.decode() + " from " + str(sock.getsockname()))
#         if not data:
#             print('\n<Client>Disconnected from server', str(sock.getsockname()))
#             sock.close()

    #i += 1
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE.encode())
socket_list = [s] # socks
i = 0

while True:
    read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

    for sock in read_sockets:
        # incoming message from remote server
        if sock == s:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                print('\nDisconnected from server')
                s.close()

            else:
                print(f"\n{data.decode()}")
                #sys.stdout.flush()

        else:
            msg = f"some msg {i}"#sys.stdin.readline()
            s.send(msg.encode())
            #sys.stdout.flush()
            i += 1