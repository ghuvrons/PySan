class HTTPError(RuntimeError):
    def __init__(self, *arg):
        if not type(arg) is tuple:
            arg = (arg, "unknown error", )
        if len(arg) == 0:
            arg = (500, "unknown error",)
        elif len(arg) == 1:
            arg = arg + ("unknown error",)
        self.args = arg
        
class WSError(RuntimeError):
    def __init__(self, *arg):
        if not type(arg) is tuple:
            arg = (arg, "unknown error", )
        if len(arg) == 0:
            arg = (500, "unknown error",)
        elif len(arg) == 1:
            arg = arg + ("unknown error",)
        self.args = arg

class PySanError(RuntimeError):
    def __init__(self, *arg):
        self.args = arg