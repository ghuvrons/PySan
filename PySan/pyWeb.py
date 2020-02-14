#!/usr/bin/env python3

import socket, sys

print(sys.argv)
command = sys.argv[1]
app = (" "+sys.argv[2]) if len(sys.argv) > 2 else ''

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 1212      # The port used by the server

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.send(command+app)
try:
    while True:
        data = s.recv(1024)
        if data:
            print(data)
        else:
            break
except KeyboardInterrupt:
    s.close()
    print("\nClosed")
