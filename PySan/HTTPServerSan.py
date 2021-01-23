from http.server import HTTPServer
from socketserver import ThreadingTCPServer
from . import ClientHandler
class HTTPServerSan(HTTPServer, ThreadingTCPServer):
    def __init__(self, host, port, RequestHandlerClass):
        HTTPServer.__init__(self, (host, port), RequestHandlerClass)
        self.applications = None
        self.server_socket = None
        self.clients = []
    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        client = self.RequestHandlerClass(request, client_address, Applications = self.applications, httpServerSan = self)
        self.clients.remove(client)