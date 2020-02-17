from __future__ import print_function
from PySan.SocketSVR import SocketSVR
from PySan.SocketFileSVR import SocketFileSVR
from PySan.ClientHandler import HTTPHandler
import traceback, sys, os, threading

# This must be the first statement before other statements.
# You may only put a quoted or triple quoted string, 
# Python comments, other future statements, or blank lines before the __future__ line.

try:
    import __builtin__
except ImportError:
    import builtins as __builtin__

def print(*args, **kwargs):
    return __builtin__.print(*args, **kwargs)

class SettingHandler(threading.Thread, SocketFileSVR):
    def __init__(self, file_path):
        threading.Thread.__init__(self)
        SocketFileSVR.__init__(self, file_path)
    def run(self):
        SocketFileSVR.run(self)
    def cmd(self, sock, cmd, app):
        pass
    def onNewClient(self, sock, addr):
        print("new setting client")
        command = sock.recv(256)
        command = command.split(' ')
        print("< ", command)
        app = command[1] if len(command) > 1 else None
        self.cmd(sock, command[0], app)

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
        main_module = sys.modules["__main__"]
        self.main_path = os.path.dirname(os.path.abspath(main_module.__file__))
    def start(self):
        self.setting = SettingHandler(self.main_path+"/setting.sock")
        self.setting.cmd = self.cmd
        self.setting.start()
        self.server = socketHandle(self.host, self.port, self.sslPort)
        self.server.clients = self.clients
        self.server.applications = self.applications
        self.server.run()
    def cmd(self, sock, cmd, app):
        try:
            if app and not cmd == 'start' and not self.applications.has_key(app):
                print("no app ", app)
                sock.shutdown(1)
                sock.close()
            if cmd == 'stream' and app:
                self.applications[app].Log.addStreamer(sock)
            elif cmd == 'list':
                sock.send(json.dumps(self.applications.keys()))
                sock.shutdown(1)
                sock.close()
            elif cmd == 'close' and app:
                sock.send(self.closeHost(app))
                sock.shutdown(1)
                sock.close()
            # elif cmd == 'reload' and app:
            #     print("reloading", app)
            #     sock.send(Applications.reloadApp(app))
            #     sock.shutdown(1)
            #     sock.close()
            # elif cmd == 'start':
            #     print("starting", app)
            #     sock.send(Applications.startApp(app))
            #     sock.shutdown(1)
            #     sock.close()
            else:
                sock.shutdown(1)
                sock.close()
        except Exception, e:
            g = traceback.format_exc()
            print(g)
    def addVHost(self, domain):
        __import__(domain)
        app_mod = sys.modules[domain]
        self.applications[domain] = getattr(app_mod, 'App')
    def closeHost(self, domain):
        try:
            self.applications[domain].close()
            del self.applications[domain]
            delattr(sys.modules[domain])
            for k in sys.modules.keys():
                if k.startswith(domain+".") and sys.modules[k] != None:
                    del sys.modules[k]
            
        except Exception as e:
            g = traceback.format_exc()
            return g
    def reloadHost(self, domain, module):
        pass
        # try:
        #     mod_name = app
        #     __import__("Applications", fromlist=[app])
        #     app_mod = getattr(sys.modules["__main__"], app)
        #     apps[app] = getattr(app_mod, 'App')
        #     return 'success'
        # except Exception as e:
        #     g = traceback.format_exc()
        #     return g
    def close(self):
        self.setting.close()
        self.server.close()
        for k in self.applications.keys():
            self.applications[k].close()
        for c in self.clients:
            try:
                c.close()
            except Exception as e:
                print("closing error", c)
                pass
