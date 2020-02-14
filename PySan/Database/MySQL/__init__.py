import MySQLdb
import threading
import time
from Connection import Connection
from Query import Query

class db:
    Q = Query
    def __init__(self, option):
        self.option = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "tes",
            "maxConnection" : 5
        }
        self.option.update(option)
        self.availableConnection = []
        self.allConnection = []
        self.queue = []
    def onAvailableConnection(self, conn):
        self.availableConnection.append(conn)
        self.shiftQueue()
    def onExpiredConnection(self, conn):
        self.allConnection.remove(conn)
        self.availableConnection.remove(conn)
    def shiftQueue(self, conn = None):
        if not conn:
            conn = self.availableConnection.pop()
        try:
            query = self.queue.pop(0)
            conn.execute(query)
        except IndexError:
            self.availableConnection.append(conn)
            pass
    def execute(self, query):
        def onError(e):
            raise e
        if type(query) is str:
            query = Query(query)
        self.queue.append(query)
        try:
            self.shiftQueue()
        except IndexError:
            if len(self.allConnection) < self.option["maxConnection"]:
                newConnection = Connection(
                    self.option["host"],
                    self.option["user"],
                    self.option["password"],
                    self.option["database"],
                    self.option["port"],
                    onAvailable = self.onAvailableConnection,
                    onExpired = self.onExpiredConnection
                )
                self.allConnection.append(newConnection)
                self.shiftQueue(newConnection)
        if query.event.wait(30):
            if not query.result and query.error:
                raise query.error
            return query.result
        else:
            self.queue.remove(query)
    def __getitem__(self, table):
        return Query(table, self)
