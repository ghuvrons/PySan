class Controller:
    def __init__(self, Databases, Services, Models, Modules, appPath = None):
        self.Databases = Databases
        self.Models = Models
        self.Modules = Modules
        self.Services = Services
        self.appPath = appPath
        