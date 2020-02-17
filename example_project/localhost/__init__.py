import sys, ssl
import Controller, Middleware, Database, Service, Module, Route
import PySan.Base.App
config = {
    "Access-Control-Allow":{
        "Origins": ['http://localhost'],
        "Credentials": True,
        "Methods": ["post", "GET", "OPTIONS"],
        "Headers": ["content-type","ggg","hhh"]
    }
}
App = PySan.Base.App(sys.modules[__name__], config)