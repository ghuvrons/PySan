from Query import Query
import MySQLdb
import threading
class Connection(threading.Thread):
    def __init__(self, host, user, password, database, port, onAvailable = None, onExpired = None):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.db = MySQLdb.connect(self.host, self.user, self.password, self.database, port=self.port)
        self.isBusy = False
        self.onAvailable = onAvailable
        self.onExpired = onExpired
    def execute(self, query):
        if self.isBusy:
            return
        try:
            cursor = self.db.cursor()
            cursor.execute(query.query)
            if query.isSelectQuery:
                results = cursor.fetchall()
            else:
                results = self.db.commit()
            query.result = results
            query.event.set()
        except Exception as e:
            if not query.isSelectQuery:
                self.db.rollback()
            query.error = e
            query.event.set()
        if self.onAvailable:
            self.onAvailable(self)
    def run():
        pass
    def close():
        db.close()
