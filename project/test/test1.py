import socket, select

# axis 1 = separate cols
# axis 0 = separate rows

host = "0.0.0.0"
port = 57279

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

#for i in range(1000,1100):
s.bind((host, port))
s.listen(1)

read_list = [s]
while True:
    readable, writable, exceptional = select.select(read_list, read_list, read_list)
    if len(readable) != 0:
        for r in readable:
            if r is r:
                client_socket, address = r.accept()
                read_list.append(client_socket)
                print('connect from:', address)
            else:
                data = r.recv(1024)
                if not data:
                    r.close()
                    read_list.remove(r)
                    #print("client disconnected")
                else: print(data)
                    
    if len(writable) != 0:
        for w in writable:
            w.send(b"python select server from Debian.\n")