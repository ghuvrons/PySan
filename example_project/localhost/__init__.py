import sys, ssl
import Controller, Middleware, Database, Service, Module, Route
import PySan.Base.App
self_module = sys.modules[__name__]
class BaseApp(PySan.Base.App):
    def __init__(self):
        self.config = {
            "Access-Control-Allow":{
                "Origins": ['http://localhost'],
                "Credentials": True,
                "Methods": ["post", "GET", "OPTIONS"],
                "Headers": ["content-type","ggg","hhh"]
            }
        }
        PySan.Base.App.__init__(self, self_module)
App = BaseApp()