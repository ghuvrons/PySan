from __future__ import print_function
from . import Base
from . import Database
from .SocketSVR import SocketSVR
from .SocketFileSVR import SocketFileSVR
from .ClientHandler import HTTPHandler
from .Base.App import App as BaseApp
from .HTTPServerSan import HTTPServerSan
import traceback, sys, os, threading, json

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

class PySan:
    def __init__(self, host = "127.0.0.1", port=3000, isSSL = False):
        self.applications = {}
        self.server = None
        self.host = host
        self.port = port
        self.isSSL = isSSL
        main_module = sys.modules["__main__"]
        self.main_path = os.path.dirname(os.path.abspath(main_module.__file__))
    def start(self):
        # self.setting = SettingHandler(self.main_path+"/setting.sock")
        # self.setting.cmd = self.cmd
        # self.setting.start()

        start_message = '''
PySan start on:
Host : {host}
Port : {port}
Mode : -
        '''
        print(start_message.format(host = self.host, port = self.port))

        HTTPHandler.protocol_version = 'HTTP/1.1'
        HTTPHandler.isSSL = self.isSSL
        self.server = HTTPServerSan(self.host, self.port, HTTPHandler)
        self.server.applications = self.applications
        self.server.serve_forever()

    def cmd(self, sock, cmd, app):
        try:
            if app and not cmd == 'start' and not app in self.applications:
                sock.send("Not found module "+app)
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
        except Exception:
            g = traceback.format_exc()
            print(g)
            
    def addVHost(self, vhosts):
        for vh in vhosts:
            _project = vhosts[vh]
            __import__(_project)
            app_mod = sys.modules[_project]
            self.applications[vh] = BaseApp(app_mod, app_mod.config)

    def closeHost(self, domain):
        try:
            self.applications[domain].close()
            del self.applications[domain]
            delattr(sys.modules[domain])
            for k in sys.modules.keys():
                if k.startswith(domain+".") and sys.modules[k] != None:
                    del sys.modules[k]
            
        except Exception:
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
        for c in self.server.clients:
            c.close()
        # self.setting.close()
        self.server.server_close()
        for k in self.applications.keys():
            self.applications[k].close()
