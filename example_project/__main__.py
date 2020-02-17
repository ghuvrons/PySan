import PySan, sys, pprint

if __name__ == "__main__":
    try:
        pySan = PySan.PySan()
        pySan.addVHost('localhost')
        keys = []
        for k in sys.modules.keys():
            keys.append(k)
        keys.sort()
        pprint.pprint(keys)
        print sys.modules["localhost.Controller.site"]
        print sys.modules["site"]
        pySan.start()
    except KeyboardInterrupt:
        pySan.close()