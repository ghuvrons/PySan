from PySan.Base.Controller import Controller
class site(Controller):
    def index(self, requestHeandler, session):
        return "Hello World"