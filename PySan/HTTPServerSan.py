from http.server import HTTPServer
from socketserver import ThreadingTCPServer
from PySan import ClientHandler
class HTTPServerSan(HTTPServer, ThreadingTCPServer):
    def __init__(self, host, port, RequestHandlerClass):
        HTTPServer.__init__(self, (host, port), RequestHandlerClass)
        self.applications = None
        self.server_socket = None
    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        self.RequestHandlerClass(request, client_address, Applications = self.applications, httpServerSan = self)
class HTTPsServerSan(HTTPServerSan):
    pass
