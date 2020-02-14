class allowOrigin:
    def __init__(self, origin = ['*']):
        self.origin = ''
        flag = True
        for o in origin:
            if flag:
                flag = False
            else:
                self.origin += ', '
            self.origin += str(o) 
    def run(self, requestHeandler):
        requestHeandler.set_respone_header('Access-Control-Allow-Origin', self.origin)
        return True
class allowCredentials:
    def __init__(self, isAllow = False):
        self.isAllow = isAllow
    def run(self, requestHeandler):
        if self.isAllow:
            requestHeandler.set_respone_header('Access-Control-Allow-Credentials', "true")
        else:
            requestHeandler.set_respone_header('Access-Control-Allow-Credentials', "false")
        return True