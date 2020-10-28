import socket,os
import select

class SocketFileSVR:
    def __init__(self, file_path):
        self.file_path = file_path
        try:
            os.remove(self.file_path)
        except OSError:
            pass
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(file_path)
        self.server_socket.listen(3)
        self.server_socket.settimeout(100)
        self.connection_list = [self.server_socket]
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
    def onCloseClient(self, sock):
        print("close client")
    def onMessage(self, msg, sock):
        print(msg)
    def run(self):
        os_input = [self.rpipe, self.server_socket]
        while not self.isClosed:
            readable = select.select(os_input, [], os_input)[0]
            for r in readable:
                if r == self.server_socket:
                    try:
                        sock, addr = self.server_socket.accept()
                    except socket.timeout:
                        continue
                    except Exception:
                        continue
                    self.onNewClient(sock, addr)
                else:
                    r.read(1)
                    break
        self.wpipe.close()
        self.rpipe.close()
        try:
            os.remove(self.file_path)
        except OSError:
            pass   
    def close(self):
        self.wpipe.write("g")
        self.wpipe.flush()
        self.server_socket.close()
        self.isClosed = True
