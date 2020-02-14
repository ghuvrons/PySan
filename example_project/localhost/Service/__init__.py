from .. import Database
serviceList = [
    'EmailManager'
]
for c in serviceList:
    __import__(c,  globals=globals())

services = {}
services["email"] = EmailManager.EmailManager()
for k in services.keys():
    services[k].Databases = Database.databases
    services[k].start()
def close():
    for k in services.keys():
        services[k].close()