from assets.currentDatetime import current_dateTime
from assets.errorHandler import checkError
import smtplib
from pprint import pprint

class SystemHandler():

    def __init__(self, system, liveWorkload):
        self.system = system
        self.liveWorkload = liveWorkload
        self.levelCheck = True

    def __call__(self):
        foundObj = {
            "date" : current_dateTime("Date"),
            "accumulated_calls" : 0,
            "accumulated_units" : 0,
            "accumulated_on_call_time" : 0,
            "accumulated_drive_time" : 0,
            "accumulated_post_time" : 0,
            "accumulated_past_eos" : 0,
            "accumulated_late_calls" : 0,
            "accumulated_level_zero" : 0,
            "systemLog" : []
        }

        Found = self.system.find_one({"date" : current_dateTime("Date")})

        if not Found:
            fallOver = self.liveWorkload.count_documents({})
            foundObj["accumulated_units"] = fallOver
            self.system.insert_one(foundObj)

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

        self.snapShotObject = obj

    @checkError
    def Notify(self, data):
        FROM_EMAIL = "EMSA.Unit.Workload@gmail.com"
        TO_EMAIL = "9183735921@email.uscc.net"
        PASSWORD = "Aubree673"
        
        server = smtplib.SMTP( "smtp.gmail.com", 587 )
        server.starttls()
        server.login(FROM_EMAIL, PASSWORD)
        
        dT = type(data)

        if dT == str:
            server.sendmail( FROM_EMAIL, TO_EMAIL, data)
            print(f"[MESSAGE SENT] {data}")
            
        elif dT == list:
            for msg in data:
                server.sendmail( FROM_EMAIL, TO_EMAIL, msg)
                print(f"[MESSAGE SENT] {msg}")

    @checkError
    def Log(self, data):
        dT = type(data)

        self.snapShot()

        obj = self.snapShotObject

        if dT == list: 
            for msg in data:

                obj["log"] = f"{msg} - {current_dateTime('Time')}"

                self.system.update_one({"date" : current_dateTime("Date")}, 
                {"$push" : {"systemLog" : obj}}
                , upsert=False)
        elif dT == str:

            obj["log"] = f"{data} - {current_dateTime('Time')}"

            self.system.update_one({"date" : current_dateTime("Date")}, 
            {"$push" : {"systemLog" : obj}}
            , upsert=False)

    @checkError
    def accumulatedUnits(self):
        self.system.update_one({"date" : current_dateTime("Date")},
        {"$inc": {"accumulated_units" : 1}}, upsert=False)

    @checkError
    def accumulatedCalls(self):
        self.system.update_one({"date" : current_dateTime("Date")},
        {"$inc": {"accumulated_calls" : 1}}, upsert=False)

    @checkError
    def accumulatedOnCallTime(self):
        self.system.update_one({"date" : current_dateTime("Date")},
        {"$inc": {"accumulated_on_call_time" : 1}}, upsert=False)

    @checkError
    def accumulatedPostTime(self):
        self.system.update_one({"date" : current_dateTime("Date")},
        {"$inc": {"accumulated_post_time" : 1}}, upsert=False)

    @checkError
    def accumulatedDriveTime(self):
        self.system.update_one({"date" : current_dateTime("Date")},
        {"$inc": {"accumulated_drive_time" : 1}}, upsert=False)

    @checkError
    def accumulatedLateCalls(self):
        self.system.update_one({"date" : current_dateTime("Date")},
        {"$inc": {"accumulated_late_calls" : 1}}, upsert=False)

    @checkError
    def accumulatedPastEOS(self):
        self.system.update_one({"date" : current_dateTime("Date")},
        {"$inc": {"accumulated_past_eos" : 1}}, upsert=False)

    @checkError
    def accumulatedLevelZero(self, csvData):
        zero = [i["unit"] for i in csvData if i["status"] == "Driving" or i["status"] == "Posting" or i["status"] == "SOS"]

        if len(zero) == 0:
            if self.levelCheck:
                msg = "System is Level Zero"
                self.Notify(msg)
                self.Log(msg)
                self.levelCheck = False
            
            Found = self.system.find_one({"date" : current_dateTime("Date")})

            if Found:
                self.system.update_one({"date" : current_dateTime("Date")}, {"$inc": {"accumulated_level_zero" : 1}}, upsert=False)
        else:
            self.levelCheck = True