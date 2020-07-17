from PySan.Base.Model import Model

class Book(Model):
    DB = "db1"
    TABLE = "book"
    def _attributtes(self):
        return {
            'name' : Model._string(),
            'number_of_pages' : Model._integer(20),
            'student' : Model._hasOne(Student, on={'nip_student' : 'nip'})
        }

class Student(Model):
    DB = "db1"
    TABLE = "student"
    def _attributtes(self):
        self._primary_key = 'nip'
        return {
            'nip' : Model._integer(),
            'name' : Model._string(),
            'ipk': Model._float(0),
            'birth_day' : Model._date(),
            # 'age' : Model._integer(20),
            # 'cars' : Model._array(),
            # 'items' : Model._object({
            #     "price" : 1000,
            #     "desc" : ""
            # }),
            'books' : Model._hasMany(Book, on={'nip' : 'nip_student'}),
            'ability' : Model._hasObject(
                Ability, 
                on={'nip' : 'nip_student'},
                key="key"
            ),
        }

class Ability(Model):
    DB = "db1"
    TABLE = "ability"
    def _attributtes(self):
        return {
            'key' : Model._string(),
            'value' : Model._string(),
            'nip_student' : Model._integer(),
            'student' : Model._hasOne(Student, on={'nip_student' : 'nip'})
        }