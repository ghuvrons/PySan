from ErrorHandler import WSError
from . import Websck
import traceback
import ssl, json, cgi
from Applications import apps as Apps

class WsClientHandler(Websck.ClientHandler):
    def __init__(self, client_sock, client_address, isSSL = False):
        self.isSSL = isSSL
        client_sock.settimeout(100)
        self.client_sock = client_sock
        self.client_address = client_address
        Websck.ClientHandler.__init__(self, client_sock, client_address)
        self.hostname = None
        self.app = None
    def servername_callback(self, sock, req_hostname, cb_context, as_callback=True):
        self.hostname = req_hostname
        try:
            app = Apps.get(req_hostname)
            context = app.ssl_context
            sock.context = context
        except:
            pass
 
    def run(self):
        try:
            if self.isSSL:
                context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
                context.set_servername_callback(self.servername_callback)
                context.load_cert_chain(certfile="/etc/ssl/certs/ssl-cert-snakeoil.pem",
                                        keyfile="/etc/ssl/private/ssl-cert-snakeoil.key")
                self.client_sock = context.wrap_socket(
                    self.client_sock, 
                    server_side=True
                )
        except Exception as e:
            traceback.print_exc()
            print("error", e)
            self.client_sock.shutdown(1)
            self.onClose(self)
            self.client_sock.close()
            return
        
        self.sock = self.client_sock
        Websck.ClientHandler.run(self)
        self.onClose(self)
        self.client_sock.close()
    def onClose(self, s):
        pass
    def middlingWare(self, middleware):
        middleware_has_run = []
        for mw in middleware:
            if mw in middleware_has_run:
                continue
            middleware_has_run.append(mw)
            if mw.func_code.co_argcount == 3:
                self.session = self.session if self.session else self.app.Session.create(self)
                if not mw(self, self.session):
                    raise WSError(500)
            elif mw.func_code.co_argcount == 2:
                if not mw(self):
                    raise WSError(500)
            else:
                if not mw():
                    raise WSError(500)
    def sendRespond(self, respMessage, code = 200, respData = None):
        resp = {
            "respond": respMessage,
            "code": code,
            "data": respData
        }
        self.sendMessage(json.dumps(resp))