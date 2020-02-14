import socket
import base64
import thread
import select
import ssl
import traceback
import os

class SocketSVR:
    def __init__(self, ip, port, ssl_port = None):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((ip, port))
        self.server_socket.listen(50)
        self.server_socket.settimeout(100)
        self.connection_list = [self.server_socket]
        self.ssl_server_socket = None
        if type(ssl_port) == int and ssl_port != port:
            self.ssl_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ssl_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.ssl_server_socket.bind((ip, ssl_port))
            self.ssl_server_socket.listen(50)
            self.ssl_server_socket.settimeout(100)
        self.client_sock = []
        self.init()
        self.isClosed = False
        r, w = os.pipe()
        self.rpipe, self.wpipe = (os.fdopen(r), os.fdopen(w, 'w'))
    def init(self):
        pass
    def sendMessage(self, s, sock):
        sock.send(s)
    def closeSocket(self, sock):
        self.onCloseClient(sock)
        self.connection_list.remove(sock)
        try:
            sock.close()
        except Exception:
            pass
    def onNewClient(self, sock, addr):
        print("new client")
    def onNewSSLClient(self, sock, addr):
        print("new client")
    def onCloseClient(self, sock):
        print("close client")
    def onMessage(self, msg, sock):
        print(msg)
        #self.sendMessage("sercer> "+msg, sock)
    def run(self):
        os_input = [self.rpipe, self.server_socket]
        if self.ssl_server_socket != None:
            os_input.append(self.ssl_server_socket)
        while not self.isClosed:
            readable, writable, exceptional = select.select(os_input, [], os_input)
            for r in readable:
                if r == self.server_socket:
                    try:
                        sock, addr = self.server_socket.accept()
                    except socket.timeout, e:
                        continue
                    except Exception, e:
                        continue
                    self.onNewClient(sock, addr)
                elif r == self.ssl_server_socket:
                    try:
                        sock, addr = self.ssl_server_socket.accept()
                    except socket.timeout, e:
                        continue
                    except Exception, e:
                        continue
                    self.onNewSSLClient(sock, addr)
                else:
                    r.read(1)
                    break
        self.wpipe.close()
        self.rpipe.close()
    def close(self):
        self.wpipe.write("g")
        self.wpipe.flush()
        self.server_socket.close()
        if self.ssl_server_socket != None:
            self.ssl_server_socket.close()            
        self.isClosed = True
