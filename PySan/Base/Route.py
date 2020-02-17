import re, pprint

class Route:
    def group(self,path,middleware=[], group=[]):
        return {'path': path, 'middleware': middleware, 'sub': [ x for x in group]}
    def route(self,path,controller,method=['get', 'post'],middleware=[], respond=None):
        return {'path': path, 'controller': controller, 'methods': method, 'middleware':middleware, "respond":respond}

class Router:
    def __init__(self):
        self.methods = {
            #"get": {"controller": ..., middleware: []},
            #"post": {},
            #"ws": {},
        }
        self.sub = {
            #"sub_path": router
        }
        self.sub_regrex = [
            #(regex, variables, router, ) # regex = reroute
        ]
    def search(self, url, method='get', isGetRespond = False):
        if type(url) == str:
            method = method.lower()
            url = url.split('/')
            while True:
                try:
                    url.remove('')
                except:
                    break
                    
        if len(url) == 0:
            if self.methods.has_key(method):
                if isGetRespond:
                    return self.methods[method]['middleware'], self.methods[method]['controller'], {}, self.methods[method]['respond'];
                else:
                    return self.methods[method]['middleware'], self.methods[method]['controller'], {};
            else: return ([], None, {}, None) if isGetRespond else ([], None, {})
        current_url = url.pop(0)
        if self.sub.has_key(current_url):
            result = self.sub[current_url].search(url, method, isGetRespond=isGetRespond)
            if result[1]: #found
                return result
        
        for regex,variables,_router in self.sub_regrex:
            matchObj = re.match('^'+regex+'$', current_url)
            if matchObj:
                data = {}
                i = 0
                for key in variables:
                    i+=1
                    data[key] = matchObj.group(i)
                result = _router.search(url, method, isGetRespond=isGetRespond)
                if result[1]: #found
                    result[2].update(data)
                    return result
        return ([], None, {}, None) if isGetRespond else ([], None, {})
        
    def createRoute(self, path, methods, controller, middleware, respond = None):
        if len(path) == 0:
            for method in methods:
                method = method.lower()
                if not self.methods.has_key(method):
                    self.methods[method] = {'controller': controller, 'middleware': [], 'respond': respond}
                for mw in self.methods[method]['middleware']:
                    if mw in middleware:
                        middleware.remove(mw)
                self.methods[method]['middleware'].extend(middleware)
        else: 
            current_path = path.pop(0)
            if re.search(r'{[^{}?]+\??([^{}]+({\d+\,?\d*})?)*}', current_path):
                print("this path is regex")
                
                def dashrepl(matchobj):
                    print(matchobj.group(0))
                    m = re.match(r"{[^{}?]+\?((?:[^{}]+(?:{\d+\,?\d*})?)+)}", matchobj.group(0))
                    if m:
                        return '('+m.group(1).replace('(', '(?:')+')'
                    else:
                        return '(.*)'
                def replaceSpesChar(s):
                    spesChar = ['(',')','[',']','<','>','?','+','\\','*','.','!','$','^','\|']
                    level = 0
                    result = ''
                    for c in s:
                        if c == '{': level+=1;
                        elif c == '}': level-=1;
                        if level==0 and c in spesChar:
                            result += '\\'
                        result += c
                    return result
                regex_current_path = replaceSpesChar(current_path)
                revar = re.sub(r'{[^{}?]+\??([^{}]+({\d+\,?\d*})?)*}', '{([^{}?]+)\??(?:[^{}]+(?:{\d+\,?\d*})?)*}', regex_current_path)
                variables = []
                m = re.match(r'^'+revar+'$', current_path)
                if m:
                    i = 0
                    while True:
                        try:
                            i+=1
                            variables.append(m.group(i))
                        except:
                            break
                regex = re.sub(r'{[^{}?]+\??([^{}]+({\d+\,?\d*})?)*}', dashrepl, regex_current_path)
                tmp = (regex, variables, Router())
                self.sub_regrex.append(tmp)
                tmp[2].createRoute(path, methods, controller, middleware, respond)
            else:
                if not self.sub.has_key(current_path):
                    self.sub[current_path] = Router()
                self.sub[current_path].createRoute(path, methods, controller, middleware, respond)
        return self

class BaseRoute:
    def __init__(self, app_module, route_config, isWsRoute = False):
        self.router = Router()
        self.isWsRoute = isWsRoute
        self.Controller = app_module.Controller
        self.controllerCache = {}
        self.Middleware = app_module.Middleware
        self.middlewareCache = {}
        self.Database = app_module.Database
        self.Module = app_module.Module if 'Module' in dir(app_module) else None
        self.Service = app_module.Service
        self.appPath = app_module.__path__[0]
        self.group(route_config)
        
    def group(self, route_config, parent_path = '/', conf_middleware=[]):
        for conf in route_config:
            if conf.has_key("controller"):
                path_arr = (parent_path+'/'+conf['path']).split('/')
                while True:
                    try:
                        path_arr.remove('')
                    except:
                        break
                controller = self.controllerToCallable(conf['controller'])
                middleware = []
                for mw in conf_middleware+conf['middleware']:
                    mw = self.middlewareToCallable(mw)
                    if mw not in middleware:
                        middleware.append(mw)
                self.router.createRoute(path_arr, conf['methods'], controller, middleware, conf['respond'])
            elif conf.has_key("sub"):
                self.group(
                    conf['sub'], 
                    (parent_path+'/'+conf['path']), 
                    conf_middleware+(conf['middleware'] if conf.has_key('middleware') else [])
                )
    def controllerToCallable(self, controller):
        if type(controller) == str:
            controller = controller.split('@', 1)
            controller_class_name = controller[0].split('/')
            if not self.controllerCache.has_key(controller[0]):
                controller_class = self.Controller
                for c_class_name in controller_class_name:
                    controller_class = getattr(controller_class, c_class_name)
                self.controllerCache[controller[0]] = controller_class(self.Database, self.Service, self.Module, self.appPath)
            return getattr(self.controllerCache[controller[0]], controller[1])
        elif callable(controller):
            return controller
        return None
    
    def middlewareToCallable(self, middleware):
        if type(middleware) == str:
            middleware = middleware.split('@', 1)
            middleware_class_name = middleware[0].split('/')
            if not self.middlewareCache.has_key(middleware[0]):
                middleware_class = self.Middleware
                for mw_class_name in middleware_class_name:
                    middleware_class = getattr(middleware_class, mw_class_name)
                self.middlewareCache[middleware[0]] = middleware_class()
            return getattr(self.middlewareCache[middleware[0]], middleware[1])
        elif callable(middleware):
            return middleware
        return None