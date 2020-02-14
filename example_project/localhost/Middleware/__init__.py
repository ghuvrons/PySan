_listMiddleware = ["header", 'auth']

for c in _listMiddleware:
    __import__(c,  globals=globals())
_Middleware ={}