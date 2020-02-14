import smtplib
import email.message
import traceback

class Email:
    def __init__(self, name, email_address, email_password):
        self.smtpServerAddress = 'citrapay.com'
        self.smtpServerPort = 2525
        self.name = name
        self.email = email_address
        self.password = email_password
        
    def send(self, to, subject, content, contentType):
        msg = email.message.Message()
        msg['Subject'] = subject
        msg['From'] = self.name+' <'+self.email+'>'
        msg['To'] =  to
        
        msg.add_header('Content-Type', contentType)
        msg.set_payload(content)
        
        s = smtplib.SMTP(self.smtpServerAddress, self.smtpServerPort)
        s.starttls()
        
        # Login Credentials for sending the mail
        s.login(self.email, self.password)
        result = False
        try:
            s.sendmail(self.email, [msg['To']], msg.as_string())
            result = True
        except:
            traceback.print_exc()
            pass
        return result
admin_email = Email('Moh Gupron', 'ghuvrons@citrapay.com', 'password')