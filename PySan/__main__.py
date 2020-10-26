#!/usr/bin/env python3

import socket, sys

# print sys.argv
command = sys.argv[1]
app = (" "+sys.argv[2]) if len(sys.argv) > 2 else ''

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect("setting.sock")
s.send((command+app).encode('UTF8'))
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
