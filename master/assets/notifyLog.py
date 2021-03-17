from assets.env import FROM_EMAIL, TO_EMAIL, PASSWORD

from assets.errorHandler import checkError
from assets.currentDatetime import current_dateTime

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from termcolor import colored
import threading

class NotifyLog():

    def __init__(self, system, liveWorkload):
        self.FROM_EMAIL = FROM_EMAIL
        self.TO_EMAIL = TO_EMAIL
        self.PASSWORD = PASSWORD
        self.system = system
        self.liveWorkload = liveWorkload

    @checkError
    def __call__(self, data, log=True, notify=True):
        self.server = smtplib.SMTP( "smtp.gmail.com", 587 )
        self.data = data
        self.log = log
        self.notify = notify 
        self.dataType = type(self.data)

        t1 = threading.Thread(target=self.Notify)
        t2 = threading.Thread(target=self.Log)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

    @checkError
    def Notify(self):
        if self.notify:
            self.server.starttls()
            self.server.login(self.FROM_EMAIL, self.PASSWORD)

            if self.dataType == str:
            
                msg = MIMEMultipart()  # create a message
                msg['From'] = self.FROM_EMAIL
                msg['To'] = self.TO_EMAIL
                msg['Subject'] = "[SYSTEM ALERT]"
                msg.attach(MIMEText(self.data, 'plain'))
                self.server.send_message(msg)
                del msg
                print(colored(f"[MESSAGE SENT] {self.data}", "yellow"))
                
            # STOP NOTIFICATIONS FOR EVERYTHING EXCEPT CSV FILE NOT FOUND
            # elif self.dataType == list:
            #     for message in self.data:
            #         msg = MIMEMultipart()  # create a message
            #         msg['From'] = self.FROM_EMAIL
            #         msg['To'] = self.TO_EMAIL
            #         msg['Subject'] = "[SYSTEM ALERT]"
            #         msg.attach(MIMEText(message, 'plain'))
            #         self.server.send_message(msg)
            #         del msg
            #         print(colored(f"[MESSAGE SENT] {message}", "yellow"))

            self.server.quit()

    @checkError
    def snapShot(self):
        driving = self.liveWorkload.find({"status" : "Driving"}).count()
        posting = self.liveWorkload.find({"status" : "Posting"}).count()
        sos = self.liveWorkload.find({"status" : "SOS"}).count()

        level = driving + posting + sos

        obj = {
            "driving" : driving,
            "posting" : posting,
            "level" : level,
            "log" : None
        }

        return obj
    
    @checkError
    def Log(self):
        if self.log:

            obj = self.snapShot()

            if self.dataType == list: 
                for msg in self.data:

                    obj["log"] = f"{msg} - {current_dateTime('Time')}"

                    self.system.update_one({"date" : current_dateTime("Date")}, 
                    {"$push" : { "logs" : obj }}
                    , upsert=False)
            elif self.dataType == str:

                obj["log"] = f"{self.data} - {current_dateTime('Time')}"

                self.system.update_one({"date" : current_dateTime("Date")}, 
                {"$push" : { "logs" : obj }}
                , upsert=False)