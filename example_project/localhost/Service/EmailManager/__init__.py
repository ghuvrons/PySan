from PySan.Base.Service import Service
import Email
import pickle, os

mail_template = {
    "email verification":
"""ILDC - Verify Your Email Address

{{salam}}.
Please input this code to verify your email:

Code : {{code}}

Thank you,
ILDC teams"""
    
}

class EmailManager(Service):
    def __init__(self):
        Service.__init__(self)
        self.queueEmail = []
        self.mail_template = mail_template
    def send(self, email):
        self.queueEmail.append(email)
    def applyTemplate(self, template, data):
        result = template
        for k in data.keys():
            result = result.replace("{{"+k+"}}", data[k])
        return result
    def run(self):
        print("starting EmailManager service")
        while not self.isClose.wait(5):
            while len(self.queueEmail) > 0:
                try:
                    email = self.queueEmail.pop(0)
                    contentType = email['content-type'] if email.has_key('content-type') else 'text/plain; charset=utf-8'
                    Email.admin_email.send(email['to'], email['subject'], email['content'], contentType)
                except:
                    pass
        print("EmailManager service closed")
        