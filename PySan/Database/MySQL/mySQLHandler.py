import MySQLdb
import threading
import time

class timeoutCounter(threading.Thread):
	def __init__(self, sqlHandler, timeout = 60):
		threading.Thread.__init__(self)
		self.sqlHandler = sqlHandler
		self.firstSetTO = timeout
		self.timeout = timeout

	def run(self):
		while True:
				time.sleep(1)
				self.timeout -= 1
				if self.timeout <= 0:
					break;
		
		self.sqlHandler.close()
		self.sqlHandler.db = None
		self.sqlHandler.tc = None

	def refresh(self):
		self.timeout = self.firstSetTO

class mySQLHandler:
	def __init__(self, host, user, password, database, timeout = 60, isLog = False, port = 3306):
		self.host = host
		self.port = port
		self.user = user
		self.password = password
		self.database = database
		self.timeout = timeout
		self.db = None
		self.tc = None
		self.isLog = isLog
		self.selectFunction = [self.now, self.count]
	
	def newConnection(self):
		#if self.db and self.tc:
		#	self.tc.refresh()
		#	return
		#self.db = MySQLdb.connect(self.host, self.user, self.password, self.database, port=self.port)
		#self.tc = timeoutCounter(self, self.timeout)
		#self.tc.start()
		return MySQLdb.connect(self.host, self.user, self.password, self.database, port=self.port)

	def db_insert(self, table, data, addquery = ''):
		col = " (";
		val = " (";
		flag = False
		for key in data.keys():
			if flag:
				col += ","
				val += ","
			else:
				flag = True
			col += '`'+key+'`'
			if type(data[key]) is str:
				val += "'"+data[key].replace('\'', '\'\'')+"'"
			elif type(data[key]) is type(self.now):
				val += data[key]()
			elif data[key] == None:
				val += "NULL"
			else:
				val += str(data[key])
		col += ") ";
		val += ") ";
		sql = "INSERT INTO "+table+col+"VALUES"+val+' '+addquery
		try:
			db = self.newConnection()
			self.execute(db, sql)
			db.commit()
			return True
		except:
			if self.isLog:
				print(sql)
			db.rollback()
			return False
		finally:
		    db.close()
	
	def db_update(self, table, data,  _where = "true"):
		str_data = " ";
		flag = False
		for key in data.keys():
			if flag:
				str_data += ","
			else:
				flag = True
			str_data += '`'+key+'`'+" = "
			if type(data[key]) is str:
				str_data += "'"+data[key].replace('\'', '\'\'')+"'"
			elif type(data[key]) is type(self.now):
				val += data[key]()
			elif data[key] == None:
				str_data += "NULL"
			else:
				str_data += str(data[key])
				
		sql = "UPDATE "+table+" SET "+str_data+" WHERE "+_where
		try:
			db = self.newConnection()
			self.execute(db, sql)
			db.commit()
			return True
		except:
			if self.isLog:
				print(sql)
			db.rollback()
			return False
		finally:
		    db.close()
			
	def db_delete(self, table, _where = "false"):				
		sql = "DELETE FROM "+table+" WHERE "+_where
		try:
			db = self.newConnection()
			self.execute(db, sql)
			db.commit()
			return True
		except:
			if self.isLog:
				print(sql)
			db.rollback()
			return False
		finally:
		    db.close()
	
	def db_select(self, table, cols=[] ,  _where = "true"):
		column=''
		if len(cols) == 0:
			column = '*'
		flag = False
		for col in cols:
			if flag:
				column += ","
			else:
				flag = True
			column += col
		sql = "SELECT "+column+" FROM "+table+" WHERE "+_where
		try:
			db = self.newConnection()
			cursor = self.execute(db, sql)
			results = cursor.fetchall()
			return results
		except:
			if self.isLog:
				print(db)
				print(sql)
			return False
		finally:
		    db.close()
			
	def execute(self, db, sql):
		cursor = db.cursor()
		cursor.execute(sql)
		return cursor
	def now(self):
		return "NOW()"
	def count(self, _param):
		return "COUNT("+_param+")"
	def string_validation(self, s):
		pass
	def close(self):
		self.db.close()