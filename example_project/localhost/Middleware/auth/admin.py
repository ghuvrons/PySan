from PySan.ErrorHandler import WSError

class isAdmin():
    def run(self, requestHeandler, session):
        if not session.getData('username'):
            raise WSError((511, 'who are you?', ))
        return True