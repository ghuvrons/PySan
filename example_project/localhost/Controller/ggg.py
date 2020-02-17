from PySan.Base.Controller import Controller
import gzip
from StringIO import StringIO
class ggg(Controller):
    def readFile(self, requestHeandler, session):
        result = ''
        basepath = requestHeandler.app.appPath+'/Public'
        f = open(basepath+'/tes.html', 'rb')
        #result = gzip.zlib.compress(result)
        #print gzip.zlib.decompress(result)
        return f
    def writeFile(self, requestHeandler, session):
        f = requestHeandler.message['file_input']
        _id = requestHeandler.message.getvalue('id')
        return 0
    def tesMysql(self, requestHeandler):
        self.Databases["vpn_radius"].execute(
            "SELECT * from userrs"
        )
        return 0