from .ErrorHandler import PySanError, HTTPError, WSError
import traceback
import threading
import socket
import mimetypes
import os, ssl, json, cgi, decimal
from inspect import signature
from . import Websck
from http.server import BaseHTTPRequestHandler, HTTPStatus

def encode_complex(obj): 
    if isinstance(obj, complex): 
        return [obj.real, obj.imag] 
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError(repr(obj) + " is not JSON serializable.") 

class HTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, client_sock, client_address, Applications = {}, httpServerSan = None):
        if Applications == {}:
            raise PySanError("Application module is not set yet.")
        self.Applications = Applications
        client_sock.settimeout(100) 
        self.respone_headers = {}
        self.hostname = None
        self.app = None
        self.session = None
        self.ws = None
        self.client_sock = client_sock
        self.httpServerSan = httpServerSan
        self.httpServerSan.clients.append(self)
        self.isSetupSuccess = True
        self.isSSL = False
        BaseHTTPRequestHandler.__init__(self, client_sock, client_address, self.httpServerSan.server_socket)

    def servername_callback(self, sock, req_hostname, cb_context, as_callback=True):
        self.hostname = req_hostname
        try:
            app = self.Applications.get(req_hostname, self.Applications['locallhost'])
            sock.context = app.ssl_context
            self.isSSL = True
        except Exception:
            g = traceback.format_exc()
            print("ssl error", g)
        
    def setup(self):
        try:
            context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
            context.set_servername_callback(self.servername_callback)
            if self.isSSL:
                context.load_cert_chain(certfile="/etc/ssl/certs/ssl-cert-snakeoil.pem",
                                        keyfile="/etc/ssl/private/ssl-cert-snakeoil.key")
                self.client_sock = context.wrap_socket(
                    self.client_sock, 
                    server_side=True
                )
        except Exception:
            g = traceback.format_exc()
            print("ssl error", g)
            # self.client_sock.shutdown(1)
            # self.onClose(self)
            # self.client_sock.close()
            self.isSetupSuccess = False
        BaseHTTPRequestHandler.setup(self)

    def onClose(self, s):
        pass

    def onEstablished(self):
        Apps = self.Applications
        if self.hostname == None:
            host = self.headers.get("Host", "").split(":")[0]
            if host != '':
                self.hostname = host
        self.app = Apps[self.hostname] if self.hostname in Apps else Apps["localhost"]

    def middlingWare(self, method, middleware):
        middleware_has_run = []
        cookies = self.app.Session.get_cookies(self)
        if self.session and ("PySessID" in cookies and self.session.id != cookies["PySessID"]):
            self.session = None
        for mw in middleware:
            if not mw and mw in middleware_has_run:
                continue
            middleware_has_run.append(mw)
            mw_arg_len = len(signature(mw)._parameters)
            if mw_arg_len == 2:
                self.session = self.session if self.session else self.app.Session.create(self)
                if not mw(self, self.session):
                    raise HTTPError(500)
            elif mw_arg_len == 1:
                if not mw(self):
                    raise HTTPError(500)
            else:
                if not mw():
                    raise HTTPError(500)

    def do_GET(self):
        self.onEstablished()
        try:
            if 'Sec-WebSocket-Key' in self.headers:
                self.ws = Websck.ClientHandler(self)
                self.ws.onMessage = self.__ws_do__
                self.session = self.app.Session.create(self)
                self.__ws_do__(json.dumps({
                    'request': "",
                    'data': None
                }), isSendRespond = False)
                self.ws.handle()
                return
            self.message = None
            self._do_('get')
        except Exception:
            traceback.print_exc()
            self.send_response_message(500, "\"unknown error\"")

    def do_POST(self):
        self.onEstablished()
        try:
            if not 'Content-Type' in self.headers:
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
        except Exception:
            traceback.print_exc()
            self.send_response_message(500, "\"unknown error\"")

    def do_OPTIONS(self):
        try:
            req_headers = self.headers["Access-Control-Request-Headers"].replace(' ', '').split(',') if "Access-Control-Request-Method" in self.headers else []
            req_method = self.headers["Access-Control-Request-Method"] if "Access-Control-Request-Method" in self.headers else None
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
        except Exception:
            traceback.print_exc()
            self.send_response_message(500, "\"unknown error\"")

    def _do_(self, method):
        try:
            log = str(self.client_address)
            log += "\n\t{}".format(self.path)
            log += "\n\t{}".format(self.hostname)
            self.app.Log.write(log)
            if os.path.exists(self.app.appPath+'/Public'+self.path):
                path = (self.app.appPath+'/Public'+self.path).replace('/../', '/')
                if os.path.isdir(path):
                    if path[-1]=='/':
                        path += 'index.html'
                    else:
                        self.set_respone_header('Location', 'http://'+self.headers.get('Host', '') + self.path+'/')
                        self.send_response_message(301)
                        return
                if os.path.isfile(path):
                    f = open(path, 'rb')
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
            controller_arg_len = len(signature(controller)._parameters)
            if controller_arg_len == 2:
                self.session = self.session if self.session else self.app.Session.create(self)
                response_message = controller(self, self.session)
            elif controller_arg_len == 1:
                response_message = controller(self)
            else:
                response_message = controller()
            self.send_response_message(200, response_message)
        except HTTPError as e:
            self.send_response_message(e.args[0], json.dumps(e.args[1]))
        except Exception:
            e = traceback.format_exc()
            print(e)
            self.app.Log.write(e)
            self.send_response_message(500, "Server error.")

    def __ws_do__(self, msg, isSendRespond = True):
        try:
            msg = json.loads(msg)
            # msg = {
            #     'request': ...
            #     'data': ...
            # }
        except ValueError:
            return
        
        if not self.app:
            Apps = self.Applications
            self.app = Apps[self.hostname] if self.hostname in Apps else Apps["localhost"]
        log = str(self.client_address)
        log += "\n\t{}".format(self.hostname)
        log += "\n\t{}".format(msg)
        self.app.Log.write(log)
        try:
            if not 'request' in msg:
                raise WSError(500)
            request = str(msg["request"])
            if not 'data' in msg:
                msg["data"] = {}
            middleware, controller, self.data, route_respond = self.app.route['ws'].search(request, isGetRespond = True)
            if not controller:
                raise WSError(404)
            self.message = msg["data"]
            self.middlingWare('ws', middleware)
            response_message = ""
            controller_arg_len = len(signature(controller)._parameters)
            if controller_arg_len == 2:
                response_message = controller(self, self.session)
            elif controller_arg_len == 1:
                response_message = controller(self)
            else:
                response_message = controller()
            if not isSendRespond and route_respond == False:
                return
            self.ws.sendRespond(route_respond if route_respond else request, 200, response_message)
        except WSError as e:
            errorCode = e.args[0]
            self.ws.sendRespond(route_respond if route_respond else request, errorCode, "Not Found.")
        except Exception:
            e = traceback.format_exc()
            self.app.Log.write(e)
            self.ws.sendRespond(route_respond if route_respond else request, 500, "Server error.")

    def _404_(self):
        self.send_response_message(404, "Not Found.")

    def handle_one_request(self):
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if not self.isSetupSuccess:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.close_connection = True
                return
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(
                    HTTPStatus.NOT_IMPLEMENTED,
                    "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            method()
            self.wfile.flush() #actually send the response if not already done.
        except socket.timeout as e:
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True
            return
    def set_respone_header(self, key, value):
        self.respone_headers[key] = value
    def send_response_message(self, code, msg = '', header_message = None):
        self.send_response(code, header_message)
        if 'name' in dir(msg):
            self.send_header("Content-Length", os.fstat(msg.fileno()).st_size)
            ext = msg.name.split('.')[-1]
            if ext in self.contentType:
                self.send_header("Content-Type", self.contentType[ext])
            else:
                ext_type = mimetypes.guess_type(msg.name)[0]
                if ext_type and ext_type.split('/')[0] == 'text':
                    self.send_header("Content-Type", 'text/plain')
                else:
                    self.send_header("Content-Type", 'application/octet-stream')
        elif self.respone_headers.get('Content-Type') == "application/json":
            msg = json.dumps(msg, default=encode_complex)
            self.send_header("Content-Length", len(msg))
        elif type(msg) == str:
            self.send_header("Content-Length", len(msg))
        else:
            msg = '{}'.format(msg)
            self.send_header("Content-Length", len(msg))
        for key in self.respone_headers.keys():
            self.send_header(key, self.respone_headers[key])
        self.end_headers()

        if 'name' in dir(msg):
            while True:
                s = msg.read()
                if s: self.client_sock.send(s)
                else: break
            self.close_connection = 1
            msg.close()
        else:
            if msg is not '':
                self.client_sock.send(msg.encode('utf-8'))
    def close(self):
        self.httpServerSan.shutdown_request(self.client_sock)
        self.close_connection = 1
    def __del__(self):
        print("client remove")
    contentType = {
        'aac': 'audio/aac',
        'abw': 'application/x-abiword',
        'arc': 'application/x-freearc',
        'avi': 'video/x-msvideo',
        'azw': 'application/vnd.amazon.ebook',
        'bin': 'application/octet-stream',
        'bmp': 'image/bmp',
        'bz': 'application/x-bzip',
        'bz2': 'application/x-bzip2',
        'csh': 'pplication/x-csh',
        'css': 'text/css',
        'csv': 'text/csv',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'eot': 'application/vnd.ms-fontobject',
        'epub': 'application/epub+zip',
        'gz': 'application/gzip',
        'gif': 'image/gif',
        'htm' :'text/html',
        'html': 'text/html',
        'ico': 'image/vnd.microsoft.icon',
        'ics': 'text/calendar',
        'jar': 'application/java-archive',
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'js': 'text/javascript',
        'json': 'application/json',
        'jsonld': 'application/ld+json',
        'mid': 'audio/midi audio/x-midi',
        'midi': 'audio/midi audio/x-midi',
        'mjs': 'text/javascript',
        'mp3': 'audio/mpeg',
        'mp4 ': 'video/mpeg',
        'mpeg ': 'video/mpeg',
        'mpkg': 'application/vnd.apple.installer+xml',
        'odp': 'application/vnd.oasis.opendocument.presentation',
        'ods': 'application/vnd.oasis.opendocument.spreadsheet',
        'odt': 'application/vnd.oasis.opendocument.text',
        'oga': 'audio/ogg',
        'ogv': 'video/ogg',
        'ogx': 'application/ogg',
        'opus': 'audio/opus',
        'otf': 'font/otf',
        'png': 'image/png',
        'pdf': 'application/pdf',
        'php': 'application/php',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'rar': 'application/x-rar-compressed',
        'rtf': 'application/rtf',
        'sh': 'pplication/x-sh',
        'svg': 'image/svg+xml',
        'swf': 'application/x-shockwave-flash',
        'tar': 'application/x-tar',
        'tif': 'image/tiff',
        'tiff': 'image/tiff',
        'ts': 'video/mp2t',
        'ttf': 'font/ttf',
        'txt': 'text/plain',
        'vsd': 'application/vnd.visio',
        'wav': 'audio/wav',
        'weba': 'audio/webm',
        'webm': 'video/webm',
        'webp': 'image/webp',
        'woff': 'font/woff',
        'woff2': 'font/woff2',
        'xhtml': 'application/xhtml+xml',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xml': 'application/xml',
        'xul': 'application/vnd.mozilla.xul+xml',
        'zip': 'application/zip',
        '3gp': 'video/3gpp',
        '3g2': 'video/3gpp2',
        '7z': 'application/x-7z-compressed'
    }