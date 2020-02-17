from PySan.Base.Log import Log
from PySan.Base.Session import SessionHandler
from PySan.Base.Route import BaseRoute

class App:
    def __init__(self, app_module, config = {}):
        self.app_module = app_module
        self.appPath = app_module.__path__[0]
        self.Log = Log()
        self.route = {
            "http": BaseRoute(self.app_module, self.app_module.Route.http.route_config).router,
            "ws": BaseRoute(self.app_module, self.app_module.Route.ws.route_config, isWsRoute=True).router
        }
        self.default_config = {
            "Session-path" : self.appPath+"/session.pkl",
            "limit": {
                "upload": 10000000, #10MB
            }
        }
        self.default_config.update(config)
        self.config = self.default_config
        self.Session = SessionHandler(self.config["Session-path"])
        self.Session.start()
    def close(self):
        self.Session.close()
        self.app_module.Service.close()
        self.app_module.Database.close()
        if 'Module' in dir(self.app_module):
            self.app_module.Module.close()