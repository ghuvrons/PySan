from HTTPRequestHandler import HTTPRequestHandler
from ErrorHandler import *
import traceback
import os, ssl, json, cgi
import Websck

class HTTPHandler(HTTPRequestHandler):
    def __init__(self, client_sock, client_address, isSSL = False, Applications = {}):
        if Applications == {}:
            raise PySanError("Application module is not set yet.")
        self.Applications = Applications
        self.isSSL = isSSL
        client_sock.settimeout(100)
        HTTPRequestHandler.__init__(self, client_sock, client_address)
        self.hostname = None
        self.app = None
        self.session = None
        self.ws = None
    def servername_callback(self, sock, req_hostname, cb_context, as_callback=True):
        self.hostname = req_hostname
        try:
            app = self.Applications.get(req_hostname)
            context = app.ssl_context
            sock.context = context
        except Exception as e:
            print(e)
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
            g = traceback.format_exc()
            print(g)
            self.client_sock.shutdown(1)
            print("closed", self.client_address)
            self.onClose(self)
            self.client_sock.close()
            return
        
        self.connection = self.client_sock
        self.rfile = self.connection.makefile('rb', self.rbufsize)
        self.wfile = self.connection.makefile('wb', self.wbufsize)
        
        self.handle()

        print("closed", self.client_address)
        self.onClose(self)
        self.connection.close()
    def onClose(self, s):
        pass
    def onEstablished(self):
        Apps = self.Applications
        self.app = Apps[self.hostname] if Apps.has_key(self.hostname) else Apps["localhost"]
    def middlingWare(self, method, middleware):
        middleware_has_run = []
        cookies = self.app.Session.get_cookies(self)
        if self.session and (cookies.has_key("PySessID") and self.session.id != cookies["PySessID"]):
            self.session = None
        for mw in middleware:
            if not mw and mw in middleware_has_run:
                continue
            middleware_has_run.append(mw)
            if mw.func_code.co_argcount == 3:
                self.session = self.session if self.session else self.app.Session.create(self)
                if not mw(self, self.session):
                    raise HTTPError(500)
            elif mw.func_code.co_argcount == 2:
                if not mw(self):
                    raise HTTPError(500)
            else:
                if not mw():
                    raise HTTPError(500)
    def do_GET(self):
        try:
            if self.headers.has_key('Sec-WebSocket-Key'):
                self.ws = Websck.ClientHandler(self)
                self.ws.onMessage = self.__ws_do__
                self.session = self.app.Session.create(self)
                self.ws.handle()
                return
            self.message = None
            self._do_('get')
        except Exception, e:
            traceback.print_exc()
            self.send_response_message(500, "\"unknown error\"")
    def do_POST(self):
        try:
            if not self.headers.has_key('Content-Type'):
                self.message = None
            elif self.headers['Content-Type'] == "application/json":
                self.message = self.rfile.read(int(self.headers['Content-Length']))
            else:
                self.message = cgi.FieldStorage(
                        fp=self.rfile, 
                        headers=self.headers,
                        environ={'REQUEST_METHOD':'POST',
                                 'CONTENT_TYPE':self.headers['Content-Type']
                        })
            self._do_('post')
        except Exception, e:
            traceback.print_exc()
            self.send_response_message(500, "\"unknown error\"")
    def do_OPTIONS(self):
        try:
            req_headers = self.headers["Access-Control-Request-Headers"].replace(' ', '').split(',') if self.headers.has_key("Access-Control-Request-Method") else []
            req_method = self.headers["Access-Control-Request-Method"] if self.headers.has_key("Access-Control-Request-Method") else None
            origin = self.headers["Origin"]
            allow_headers = ''
            allow_methods = ''
            isFirst = True
            try:
                for req_header in req_headers:
                    if not req_header in self.app.config["Access-Control-Allow"]["Headers"]:
                        continue
                    if not isFirst:
                        allow_headers += ', '
                    else:
                         isFirst = False
                    allow_headers += req_header
                if allow_headers:
                    self.set_respone_header('Access-Control-Allow-Headers', allow_headers)
            except:
                pass
            isFirst = True
            try:
                for method in self.app.config["Access-Control-Allow"]["Methods"]:
                    if not isFirst:
                        allow_methods += ', '
                    else:
                         isFirst = False
                    allow_methods += method
                if allow_methods:
                    self.set_respone_header('Access-Control-Allow-Methods', allow_methods)
            except:
                pass
            try:
                if origin in self.app.config["Access-Control-Allow"]["Origins"]:
                    self.set_respone_header('Access-Control-Allow-Origin', origin)
            except:
                pass
            try:
                if self.app.config["Access-Control-Allow"]["Credentials"]:
                    self.set_respone_header('Access-Control-Allow-Credentials', "true")
            except:
                pass
            self.send_response_message(204, 'success')
        except Exception, e:
            traceback.print_exc()
            self.send_response_message(500, "\"unknown error\"")
    def _do_(self, method):
        try:
            log = str(self.client_address)
            log += "\n\t{}".format(self.path)
            log += "\n\t{}".format(self.hostname)
            self.app.Log.write(log)
            if os.path.exists(self.app.appPath+'/Web'+self.path):
                path = (self.app.appPath+'/Web'+self.path).replace('/../', '/')
                if os.path.isdir(path):
                    print("path dir")
                    if path[-1]=='/':
                        path += 'index.html'
                    else:
                        self.set_respone_header('Location', 'http://'+self.headers.get('Host', '') + self.path+'/')
                        self.send_response_message(301)
                        return
                if os.path.isfile(path):
                    f = open(path, 'r')
                    self.send_response_message(200, f)
                    return
            middleware, controller, self.data = self.app.route['http'].search(self.path, method)
            origin = self.headers.get("Origin")
            try:
                if origin in self.app.config["Access-Control-Allow"]["Origins"]:
                    self.set_respone_header('Access-Control-Allow-Origin', origin)
            except:
                pass
            try:
                if self.app.config["Access-Control-Allow"]["Credentials"]:
                    self.set_respone_header('Access-Control-Allow-Credentials', "true")
            except:
                pass
            if not controller:
                raise HTTPError(404, 'not found')
            self.middlingWare(method, middleware)
            response_message = ""
            if controller.func_code.co_argcount == 3:
                self.session = self.session if self.session else self.app.Session.create(self)
                response_message = controller(self, self.session)
            elif controller.func_code.co_argcount == 2:
                response_message = controller(self)
            else:
                response_message = controller()
            self.send_response_message(200, response_message)
        except HTTPError, e:
            self.send_response_message(e[0], json.dumps(e[1]))
        except Exception, e:
            self.app.Log.write(traceback.format_exc())
            self.send_response_message(500, "Server error.")
    def __ws_do__(self, msg):
        
        try:
            msg = json.loads(msg)
        except ValueError:
            print([msg])
            self.sendMessage(msg)
            print("error")
            return
        
        '''
        msg = {
            'request': ...
            'data': ...
        }
        '''
        if not self.app:
            Apps = self.Applications
            self.app = Apps[self.hostname] if Apps.has_key(self.hostname) else Apps["localhost"]
        log = str(self.client_address)
        log += "\n\t{}".format(self.hostname)
        log += "\n\t{}".format(msg)
        self.app.Log.write(log)
        try:
            if not msg.has_key('request'):
                raise WSError(500)
            request = str(msg["request"])
            if not msg.has_key('data'):
                msg["data"] = {}
            middleware, controller, self.data, respond = self.app.route['ws'].search(request, isGetRespond = True)
            if not controller:
                raise WSError(404)
            self.message = msg["data"]
            self.middlingWare('ws', middleware)
            response_message = ""
            if controller.func_code.co_argcount == 3:
                self.session = self.session if self.session else self.app.Session.create(self)
                response_message = controller(self, self.session)
            elif controller.func_code.co_argcount == 2:
                response_message = controller(self)
            else:
                response_message = controller()
            self.ws.sendRespond(respond if respond else request, 200, response_message)
        except WSError as e:
            errorCode = e[0]
            self.ws.sendRespond(respond if respond else request, errorCode, "Not Found.")
        except Exception as e:
            self.app.Log.write(traceback.format_exc())
            self.ws.sendRespond(respond if respond else request, 500, "Server error.")
    def _404_(self):
        self.send_response_message(404, "Not Found.")
