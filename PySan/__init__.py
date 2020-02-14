from __future__ import print_function
from PySan.SocketSVR import SocketSVR
from PySan.ClientHandler import HTTPHandler
import traceback, sys

# This must be the first statement before other statements.
# You may only put a quoted or triple quoted string, 
# Python comments, other future statements, or blank lines before the __future__ line.

try:
    import __builtin__
except ImportError:
    import builtins as __builtin__

def print(*args, **kwargs):
    return __builtin__.print(*args, **kwargs)

class socketHandle(SocketSVR):
    def handsacking(self, sock):
        return True
    def onNewClient(self, sock, addr):
        print("new web client")
        HTTPH = HTTPHandler(sock, addr, Applications = self.applications)
        self.clients.append(HTTPH)
        HTTPH.start()
        def onClose(s):
            try:
                print("removing", addr)
                self.clients.remove(s)
                print("removed", addr)
            except:
                pass
        HTTPH.onClose = onClose
    def onNewSSLClient(self, sock, addr):
        print("new ssl web client")
        HTTPH = HTTPHandler(sock, addr, isSSL = True, Applications = self.applications)
        self.clients.append(HTTPH)
        HTTPH.start()
        def onClose(s):
            try:
                print("removing", addr)
                self.clients.remove(s)
                print("removed", addr)
            except:
                pass
        HTTPH.onClose = onClose

# appList = [
#     'localhost'
# ]
# __import__(__name__, fromlist=appList)
# apps = {}
# for app in appList:
#     app_mod = getattr(sys.modules[__name__], app)
#     apps[app] = getattr(app_mod, 'App')

class PySan:
    def __init__(self):
        self.applications = {}
        self.clients = []
        self.server = None
        self.host = "127.0.0.1"
        self.port = 8000
        self.sslPort = 8001
    def start(self):
        self.server = socketHandle(self.host, self.port, self.sslPort)
        self.server.clients = self.clients
        self.server.applications = self.applications
        self.server.run()
    def addVHost(self, domain, module):
        self.applications[domain] = getattr(module, 'App')
    def close(self):
        self.server.close()
        for k in self.applications.keys():
            self.applications[k].close()
        for c in self.clients:
            try:
                c.close()
            except Exception as e:
                print("closing error", c)
                pass
