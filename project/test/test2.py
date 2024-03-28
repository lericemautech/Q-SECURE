import socket, select                                                                                                                                

host = "0.0.0.0"
port = 57279

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
inout = [s]
i = 0

while i < 10:
    infds, outfds, err = select.select(inout, inout, [], 5)
    if len(infds) != 0:
        buf = s.recv(1024)

        if len(buf) != 0:
            i += 1
            print('receive data:', buf)

    if len(outfds) != 0:
        s.send(b"python select client from Debian.\n")