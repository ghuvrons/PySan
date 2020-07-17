from .. import Database
from .. import Service
moduleList = [
]
for c in moduleList:
    __import__(c,  globals=globals())

modules = {}

for k in modules.keys():
    modules[k].Databases = Database.databases
    modules[k].Services = Service.services