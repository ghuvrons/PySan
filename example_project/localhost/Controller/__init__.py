controllerList = ['site', 'ggg']
for c in controllerList:
    __import__(c,  globals=globals())