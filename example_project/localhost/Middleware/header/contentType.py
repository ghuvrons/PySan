class appJSON:
    def run(self, requestHeandler):
        requestHeandler.set_respone_header('Content-Type', "application/json")
        return True