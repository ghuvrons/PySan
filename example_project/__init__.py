import time, imp, sys
import traceback
appList = [
    'localhost'
]
__import__(__name__, fromlist=appList)
apps = {}
for app in appList:
    app_mod = getattr(sys.modules[__name__], app)
    apps[app] = getattr(app_mod, 'App')
def reloadApp(app):
    try:
        apps[app].close()
        del apps[app]
        delattr(sys.modules[__name__], app)
        mod_name = "Applications."+app
        for k in sys.modules.keys() :
            if k.startswith(mod_name):
                del sys.modules[k]
        __import__("Applications", fromlist=[app])
        app_mod = getattr(sys.modules[__name__], app)
        apps[app] = getattr(app_mod, 'App')
        return 'success'
    except Exception as e:
        g = traceback.format_exc()
        return g
def startApp(app):
    try:
        if apps.has_key(app):
            apps[app].close()
            del apps[app]
        try:
            delattr(sys.modules[__name__], app)
            mod_name = "Applications."+app
            for k in sys.modules.keys() :
                if k.startswith(mod_name):
                    del sys.modules[k]
        except Exception as e:
            print e
        __import__("Applications", fromlist=[app])
        app_mod = getattr(sys.modules[__name__], app)
        apps[app] = getattr(app_mod, 'App')
        return 'success'
    except Exception as e:
        g = traceback.format_exc()
        return g
def close():
    for k in apps.keys():
        apps[k].close()