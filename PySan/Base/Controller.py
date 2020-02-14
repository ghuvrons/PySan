class Controller:
    def __init__(self, Database, Service, Module, appPath = None):
        self.Databases = Database.databases if Database else None
        self.Services = Service.services if Service else None
        self.Modules = Module.modules if Module else None
        self.appPath = appPath
        