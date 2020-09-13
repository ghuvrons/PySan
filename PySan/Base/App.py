from PySan.Base.Log import Log
from PySan.Base.Session import SessionHandler
from PySan.Base.Route import BaseRoute, Route
import sys, json, pprint

class App:
    def __init__(self, app_module, config = {}):
        self.app_module = app_module
        self.appPath = app_module.__path__[0]
        self.Databases = {}
        self.Models = {}
        self.Modules = {}
        self.Services = {}
        self.route_config = {'http': [], 'ws': []}
        self.importAppSystem()
        # self.printAllModules()
        httpRouter = BaseRoute(
            self.app_module, 
        )
        wsRouter = BaseRoute(
            self.app_module, 
            isWsRoute=True
        )
        httpRouter.Databases = self.Databases
        httpRouter.Models = self.Models
        httpRouter.Modules = self.Modules
        httpRouter.Services = self.Services
        httpRouter.generateRoute(self.route_config['http'])
        wsRouter.Databases = self.Databases
        wsRouter.Models = self.Models
        wsRouter.Modules = self.Modules
        wsRouter.Services = self.Services
        wsRouter.generateRoute(self.route_config['ws'])
        self.route = {
            "http": httpRouter.router,
            "ws": wsRouter.router
        }
        
        self.default_config = {
            "Session-path" : self.appPath+"/session.pkl",
            "limit": {
                "upload": 10000000, #10MB
            }
        }
        self.Log = Log()
        self.default_config.update(config)
        self.config = self.default_config
        self.Session = SessionHandler(self.config["Session-path"])
        self.Session.start()
    def importAppSystem(self):
        app_mod_name = self.app_module.__name__
        __import__(app_mod_name, fromlist=[
            "Controller", "Middleware", "Database", "Service", "Model", "Route"
        ])

        try:
            controller_json = open(sys.modules[app_mod_name+".Controller"].__path__[0]+"/controller.json")
            controller_list = json.load(controller_json)
            controller_json.close()
            __import__(app_mod_name+".Controller", fromlist=[str(s) for s in controller_list], globals=globals())
        except Exception as e:
            pass

        try:
            middleware_json = open(sys.modules[app_mod_name+".Middleware"].__path__[0]+"/middleware.json")
            middleware_list = json.load(middleware_json)
            middleware_json.close()

            __import__(app_mod_name+".Middleware", fromlist=[str(s) for s in middleware_list], globals=globals())
        except:
            pass

        try:
            database_json = open(sys.modules[app_mod_name+".Database"].__path__[0]+"/database.json")
            database_obj = json.load(database_json)
            database_json.close()

            # __import__(app_mod_name+".Database", fromlist=[str(s) for s in middleware_list], globals=globals())
            for db_key in database_obj.keys():
                db_config = database_obj[db_key]
                __import__(db_config['driver'])
                self.Databases[db_key] = sys.modules[db_config['driver']].db(db_config['config'])
        except Exception as e:
            print(e)
            pass
        
        try:
            service_json = open(sys.modules[app_mod_name+".Service"].__path__[0]+"/service.json")
            service_obj = json.load(service_json)
            service_json.close()

            for sr_key in service_obj.keys():
                service_class_name = service_obj[sr_key].split(".")
                tmp_service_mod = app_mod_name+".Service"
                for service_mod_name in service_class_name[:-1]:
                    __import__(tmp_service_mod, fromlist=[str(service_mod_name)])
                    tmp_service_mod += "."+str(service_mod_name)
                service_class = getattr(sys.modules[tmp_service_mod], str(service_class_name[-1]))
                self.Services[sr_key] = service_class()
                self.Services[sr_key].Databases = self.Databases
                self.Services[sr_key].start()
        except Exception as e:
            print( "error : ", e)
            pass

        try:
            model_json = open(sys.modules[app_mod_name+".Model"].__path__[0]+"/model.json")
            model_obj = json.load(model_json)
            model_json.close()

            # __import__(app_mod_name+".Database", fromlist=[str(s) for s in middleware_list], globals=globals())
            for sr_key in model_obj.keys():
                model_class_name = model_obj[sr_key].split(".")
                tmp_model_mod = app_mod_name+".Model"
                for model_mod_name in model_class_name[:-1]:
                    __import__(tmp_model_mod, fromlist=[str(model_mod_name)])
                    tmp_model_mod += "."+str(model_mod_name)
                model_class = getattr(sys.modules[tmp_model_mod], str(model_class_name[-1]))
                self.Models[sr_key] = model_class
                self.Models[sr_key].Databases = self.Databases
                self.Models[sr_key].Services = self.Services
                # self.printAllModules()

                # __import__(app_mod_name+".Service", fromlist=[str(s) for s in service_class_name])
                # __import__('pprint')
                # print pprint.pprint(dir())
        except Exception as e:
            print("error : ", e)
            pass

        try:
            r = Route()
            http_router_json = open(sys.modules[app_mod_name+".Route"].__path__[0]+"/http.json")
            http_router = json.load(http_router_json)
            http_router_json.close()
            self.route_config['http'] = r.jsonToRoute(http_router)

            ws_router_json = open(sys.modules[app_mod_name+".Route"].__path__[0]+"/ws.json")
            ws_router = json.load(ws_router_json)
            ws_router_json.close()
            self.route_config['ws'] = r.jsonToRoute(ws_router)
        except Exception as e:
            print("error : ", e)
            pass

    def printAllModules(self):
        modules = sys.modules.keys()
        modules.sort()
        for m in modules:
            print(m)
    def close(self):
        self.Session.close()
        if 'Module' in dir(self.app_module) and hasattr(self.app_module.Module, 'close'):
            self.app_module.Module.close()
        if hasattr(self.app_module.Database, 'close'):
            self.app_module.Database.close()
        
        for k in self.Services.keys():
            self.Services[k].close()