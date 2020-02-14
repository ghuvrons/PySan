import threading
class Service(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.database = None
        self.isClose = threading.Event()
    def run(self):
        pass
    def close(self):
        self.isClose.set()