import sys, os, select
import threading
import time
import random
import socket # For gethostbyaddr() hm
import json, decimal
import mimetypes
from warnings import filterwarnings, catch_warnings
from ssl import SSLError
with catch_warnings():
    if sys.py3kwarning:
        filterwarnings("ignore", ".*mimetools has been removed",
                        DeprecationWarning)
    import mimetools
    
def encode_complex(obj): 
    if isinstance(obj, complex): 
        return [obj.real, obj.imag] 
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError(repr(obj) + " is not JSON serializable.") 

class HTTPRequestHandler(threading.Thread):
    sys_version = "Citrapay"

    server_version = "janoko"
    default_request_version = "HTTP/0.9"
    rbufsize = -1
    wbufsize = 0
    def __init__(self, client_sock, client_address):
        threading.Thread.__init__(self)
        #self.num_files = 0
        self.client_sock = client_sock
        self.client_address = client_address        
        self.respone_headers = {}
        self.msg = ''
        self.cookie_id = None
        self.hostname = None
    def parse_request(self):
        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        self.close_connection = 1
        requestline = self.raw_requestline
        requestline = requestline.rstrip('\r\n')
        self.requestline = requestline
        words = requestline.split()
        if len(words) == 3:
            command, path, version = words
            if version[:5] != 'HTTP/':
                self.send_error(400, "Bad request version (%r)" % version)
                return False
            try:
                base_version_number = version.split('/', 1)[1]
                version_number = base_version_number.split(".")
                if len(version_number) != 2:
                    raise ValueError
                version_number = int(version_number[0]), int(version_number[1])
            except (ValueError, IndexError):
                self.send_error(400, "Bad request version (%r)" % version)
                return False
            if version_number >= (1, 1) and self.protocol_version >= "HTTP/1.1":
                self.close_connection = 0
            if version_number >= (2, 0):
                self.send_error(505, "Invalid HTTP Version (%s)" % base_version_number)
                return False
        elif len(words) == 2:
            command, path = words
            self.close_connection = 1
            if command != 'GET':
                self.send_error(400, "Bad HTTP/0.9 request type (%r)" % command)
                return False
        elif not words:
            return False
        else:
            self.send_error(400, "Bad request syntax (%r)" % requestline)
            return False
        self.command, self.path, self.request_version = command, path, version

        # Examine the headers and look for a Connection directive
        self.headers = self.MessageClass(self.rfile, 0)
        hostname = self.headers.get('Host', "").split(':')[0]
        if self.hostname == None:
            self.hostname = hostname
        elif self.hostname != hostname:
            self.send_error(400, "Bad request")
            return False
        conntype = self.headers.get('Connection', "")
        if conntype.lower() == 'close':
            self.close_connection = 1
        elif (conntype.lower() == 'keep-alive' and self.protocol_version >= "HTTP/1.1"):
            self.close_connection = 0
        return True
        
    def parse_header(self, header):
        header_lines = header.split("\r\n")
        headers = {}
        self.raw_requestline = header_lines[0]
        for line in header_lines[1:]:
            key, value = line.split(": ")
            headers[key] = value
        return headers
    
    def parse_getForm(self):
        self.form_get = {}
        if self.path.find("?") != -1:
            self.path, get_string = self.path.split("?", 1)
            fg = get_string.split("&")
            for x in fg:
                data = x.split("=", 1)
                if len(data) == 2:
                    self.form_get[data[0]] = data[1]
                else:
                    self.form_get[data[0]] = ""

    def handle_one_request(self):
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.connection.shutdown(1)
                print("sock > no data")
                self.close_connection = 1
                return
            if not self.parse_request():
                self.connection.shutdown(1)
                self.close_connection = 1
                # An error code has been sent, just exit
                return
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(501, "Unsupported method (%r)" % self.command)
                return
            self.onEstablished()
            max_upload = 10000000
            if 'app' in dir(self):
                max_upload = self.app.config["limit"]['upload']
            if int(self.headers.get("Content-Length", '0')) > max_upload:
                self.send_error(413)
                self.connection.shutdown(1)
                self.close_connection = 1
                return
            self.parse_getForm();
            method = getattr(self, mname)
            method()
            self.wfile.flush() #actually send the response if not already done.
            self.respone_headers.clear()
        except socket.timeout, e:
            print("sock timeout>", e)
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.connection.shutdown(1)
            self.close_connection = 1
            return
        except SSLError, e:
            print("sock e ssl >", e)
            #a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.connection.shutdown(1)
            self.close_connection = 1
            return
        except Exception, e:
            print("sock some error>", e)
            self.close_connection = 1
            return
           
    def onEstablished(self):
        pass
    def handle(self):
        """Handle multiple requests if necessary."""
        self.close_connection = 1

        self.handle_one_request()
        while not self.close_connection:
            self.handle_one_request()
    def close(self):
        self.connection.shutdown(1)
    def send_error(self, code, message=None):

        try:
            short, long = self.responses[code]
        except KeyError:
            short, long = '???', '???'
        if message is None:
            message = short
        explain = long
        self.log_error("code %d, message %s", code, message)
        self.send_response(code, message)
        self.send_header('Connection', 'close')

        # Message body is omitted for cases described in:
        #  - RFC7230: 3.3. 1xx, 204(No Content), 304(Not Modified)
        #  - RFC7231: 6.3.6. 205(Reset Content)
        content = None
        if code >= 200 and code not in (204, 205, 304):
            # HTML encode to prevent Cross Site Scripting attacks
            # (see bug #1100201)
            content = (self.error_message_format % {
                'code': code,
                'message': (message),
                'explain': explain
            })
            self.send_header("Content-Type", self.error_content_type)
        self.end_headers()

        if self.command != 'HEAD' and content:
            self.client_sock.send(content)

    error_message_format = "something error"
    error_content_type = "error"

    def set_respone_header(self, key, value):
        self.respone_headers[key] = value
    def send_response_message(self, code, msg = '', header_message = None):
        self.send_response(code, header_message)
        if type(msg) == file:
            self.send_header("Content-Length", os.fstat(msg.fileno()).st_size)
            ext = msg.name.split('.')[-1]
            if self.contentType.has_key(ext):
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
        if self.headers.has_key("Connection"):
            self.send_header("Connection", self.headers["Connection"])
        for key in self.respone_headers.keys():
            self.send_header(key, self.respone_headers[key])
        self.end_headers()

        if type(msg) == file:
            ll = 0
            while True:
                s = msg.read()
                if s: self.client_sock.send(s)
                else: break
            self.close_connection = 1
            msg.close()
        else:
            self.client_sock.send(msg)

    def send_response(self, code, message=None):
        """Send the response header and log the response code.

        Also send two standard headers with the server software
        version and the current date.

        """
        self.log_request(code)
        if message is None:
            if code in self.responses:
                message = self.responses[code][0]
            else:
                message = ''
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("%s %d %s\r\n" %
                             (self.protocol_version, code, message))
            # print(self.protocol_version, code, message)
        self.send_header('Server', self.version_string())
        self.send_header('Date', self.date_time_string())

    def send_header(self, keyword, value):
        """Send a MIME header."""
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("%s: %s\r\n" % (keyword, value))

        if keyword.lower() == 'connection':
            if value.lower() == 'close':
                self.close_connection = 1
            elif value.lower() == 'keep-alive':
                self.close_connection = 0

    def end_headers(self):
        """Send the blank line ending the MIME headers."""
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("\r\n")

    def log_request(self, code='-', size='-'):
        """Log an accepted request.

        This is called by send_response().

        """

        self.log_message('"%s" %s %s',
                         self.requestline, str(code), str(size))

    def log_error(self, format, *args):
        self.log_message(format, *args)

    def log_message(self, format, *args):
        return
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.client_address,
                          self.log_date_time_string(),
                          format%args))

    def version_string(self):
        return self.server_version + ' ' + self.sys_version

    def date_time_string(self, timestamp=None):
        """Return the current date and time formatted for a message header."""
        if timestamp is None:
            timestamp = time.time()
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
        s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
                self.weekdayname[wd],
                day, self.monthname[month], year,
                hh, mm, ss)
        return s

    def log_date_time_string(self):
        """Return the current time formatted for logging."""
        now = time.time()
        year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
        s = "%02d/%3s/%04d %02d:%02d:%02d" % (
                day, self.monthname[month], year, hh, mm, ss)
        return s
    
    ''' COOKIES HANDLING '''
    def start_cookie(self):
        if not 'COOKIES' in globals():
            global COOKIES
            COOKIES = {}
        if not (self.headers.has_key("Cookie")):
            self.cookie_id = self.generate_id_cookies()
            while COOKIES.has_key(self.cookie_id):
                self.cookie_id = self.generate_id_cookies()                
            self.set_respone_header('Set-Cookie', "PHPSESSID="+self.cookie_id+"; path=/")
        else:
            self.cookie_id = self.headers["Cookie"].lstrip("PHPSESSID=");
        if not COOKIES.has_key(self.cookie_id):    
            COOKIES[self.cookie_id] = {}
        
    def set_cookie(self, key, value):
        if self.cookie_id == None:
            print("cookie not be started")
            return
        COOKIES[self.cookie_id][key] = value
    def get_cookie(self, key):
        if self.cookie_id == None:
            print("cookie not be started")
            return None
        if COOKIES[self.cookie_id].has_key(key):
            return COOKIES[self.cookie_id][key]
        else:
            return None

    def generate_id_cookies(self):
        phpsesid = ''
        for x in range(26):
            c = random.randint(1, 31)
            c2 = random.randint(0, 1)
            if(c < 27):
                if c2:
                    c = c | 64
                else:
                    c = c | 96
                phpsesid += chr(c)
            else:
                c = c % 27
                if c2:
                    c += 5
                phpsesid += str(c)
        return phpsesid

    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    monthname = [None,
                 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Essentially static class variables

    # The version of the HTTP protocol we support.
    # Set this to HTTP/1.1 to enable automatic keepalive
    protocol_version = "HTTP/1.0"

    # The Message-like class used to parse headers
    MessageClass = mimetools.Message
    
    # Table mapping response codes to messages; entries have the
    # form {code: (shortmessage, longmessage)}.
    # See RFC 2616.
    responses = {
        100: ('Continue', 'Request received, please continue'),
        101: ('Switching Protocols',
              'Switching to new protocol; obey Upgrade header'),

        200: ('OK', 'Request fulfilled, document follows'),
        201: ('Created', 'Document created, URL follows'),
        202: ('Accepted',
              'Request accepted, processing continues off-line'),
        203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
        204: ('No Content', 'Request fulfilled, nothing follows'),
        205: ('Reset Content', 'Clear input form for further input.'),
        206: ('Partial Content', 'Partial content follows.'),

        300: ('Multiple Choices',
              'Object has several resources -- see URI list'),
        301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
        302: ('Found', 'Object moved temporarily -- see URI list'),
        303: ('See Other', 'Object moved -- see Method and URL list'),
        304: ('Not Modified',
              'Document has not changed since given time'),
        305: ('Use Proxy',
              'You must use proxy specified in Location to access this '
              'resource.'),
        307: ('Temporary Redirect',
              'Object moved temporarily -- see URI list'),

        400: ('Bad Request',
              'Bad request syntax or unsupported method'),
        401: ('Unauthorized',
              'No permission -- see authorization schemes'),
        402: ('Payment Required',
              'No payment -- see charging schemes'),
        403: ('Forbidden',
              'Request forbidden -- authorization will not help'),
        404: ('Not Found', 'Nothing matches the given URI'),
        405: ('Method Not Allowed',
              'Specified method is invalid for this resource.'),
        406: ('Not Acceptable', 'URI not available in preferred format.'),
        407: ('Proxy Authentication Required', 'You must authenticate with '
              'this proxy before proceeding.'),
        408: ('Request Timeout', 'Request timed out; try again later.'),
        409: ('Conflict', 'Request conflict.'),
        410: ('Gone',
              'URI no longer exists and has been permanently removed.'),
        411: ('Length Required', 'Client must specify Content-Length.'),
        412: ('Precondition Failed', 'Precondition in headers is false.'),
        413: ('Request Entity Too Large', 'Entity is too large.'),
        414: ('Request-URI Too Long', 'URI is too long.'),
        415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
        416: ('Requested Range Not Satisfiable',
              'Cannot satisfy request range.'),
        417: ('Expectation Failed',
              'Expect condition could not be satisfied.'),

        500: ('Internal Server Error', 'Server got itself in trouble'),
        501: ('Not Implemented',
              'Server does not support this operation'),
        502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
        503: ('Service Unavailable',
              'The server cannot process the request due to a high load'),
        504: ('Gateway Timeout',
              'The gateway server did not receive a timely response'),
        505: ('HTTP Version Not Supported', 'Cannot fulfill request.'),
    }
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
    def __del__(self):
        print("class has gone")
