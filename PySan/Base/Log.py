import datetime
class Log:
    def __init__(self):
        self.isTmpFull = False
        self.tmp = []
        self.streamer = None
    def write(self, log):
        tmp = (datetime.datetime.now(), '{}'.format(log))
        if self.streamer:
            try:
                date, log = tmp
                self.streamer.send('\n'+date.strftime("%c")+'\n'+str(log))
            except:
                self.streamer = None
        self.tmp.append(tmp)
        if len(self.tmp) > 100:
            self.tmp.pop(0)
    def addStreamer(self, sock):
        print self
        for tmp in self.tmp:
            date, log = tmp
            sock.send(date.strftime("%c")+'\n'+str(log))
        self.streamer = sock