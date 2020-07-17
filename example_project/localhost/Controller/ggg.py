from PySan.Base.Controller import Controller
from PySan.Database.MySQL import Query 
import datetime
class ggg(Controller):
    def index(self, requestHeandler):
        # Create new model
        # new_student = self.Models['student'].create(name="ghuvrons", nip = 32)
        # new_student.save()
        # print new_student.nip

        students = self.Models['student'].search(nip=123)
        for s in students:
            print "-"
            print s.name
            s.name = "kikio"
            s.save()
            for book in s.books:
                print book.name

        student = self.Models['student'].one(nip=123)
        student.ability['speed'].value = "lololo"
        print student.ability.save()
        return "s1.name"