from assets.currentDatetime import current_dateTime
from assets.errorHandler import checkError
import smtplib
from pprint import pprint
import statistics

class SystemHandler():

    def __init__(self, system, liveWorkload):
        self.system = system
        self.liveWorkload = liveWorkload
        self.levelCheck = True

    def __call__(self):
        foundObj = {
            "date" : current_dateTime("Date"),
            "valid" : True,
            "accumulated_calls" : 0,
            "accumulated_units" : 0,
            "accumulated_on_call_time" : 0,
            "accumulated_drive_time" : 0,
            "accumulated_post_time" : 0,
            "accumulated_past_eos" : 0,
            "accumulated_late_calls" : 0,
            "accumulated_level_zero" : 0,
            "call_status" : None,
            "on_call_status" : None,
            "post_time_status" : None,
            "drive_time_status" : None,
            "unit_status" : None,
            "past_eos_status" : None,
            "late_call_status" : None,
            "level_zero_status" : None,
            "systemLog" : []
        }

        Found = self.system.find_one({"date" : current_dateTime("Date")})

        if not Found:
            rollOver = self.liveWorkload.count_documents({})
            foundObj["accumulated_units"] = rollOver
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

    @checkError
    def averageStatus(self):
        # get averages for all system parameters, then determine if current trend is above/below average.
        systemData = self.system.find({})

        currentHour = current_dateTime("Time").split(":")[0]

        if currentHour != "00":

            pastCalls = []
            pastPostTime = []
            pastOnCallTime = []
            pastDriveTime = []
            pastUnits = []
            pastPastEOS = []
            pastLateCalls = []
            pastLevelZero = []
            currentCalls = 0
            currentPostTime = 0
            currentOnCallTime = 0
            currentDriveTime = 0
            currentUnits = 0
            currentPastEOS = 0
            currentLateCalls = 0
            currentLevelZero = 0
            for data in systemData:
                if data["valid"]:
                    if data["date"] != current_dateTime("Date"):
                        pastCalls.append(data["accumulated_calls"])
                        pastPostTime.append(data["accumulated_post_time"])
                        pastOnCallTime.append(data["accumulated_on_call_time"])
                        pastDriveTime.append(data["accumulated_drive_time"])
                        pastUnits.append(data["accumulated_units"])
                        pastPastEOS.append(data["accumulated_past_eos"])
                        pastLateCalls.append(data["accumulated_late_calls"])
                        pastLevelZero.append(data["accumulated_level_zero"])
                    else:
                        currentCalls = data["accumulated_calls"]
                        currentPostTime = data["accumulated_post_time"]
                        currentOnCallTime = data["accumulated_on_call_time"]
                        currentDriveTime = data["accumulated_drive_time"]
                        currentUnits = data["accumulated_units"]
                        currentPastEOS = data["accumulated_past_eos"]
                        currentLateCalls = data["accumulated_late_calls"]
                        currentLevelZero = data["accumulated_level_zero"]

            avgPastCalls = round(statistics.mean(pastCalls))
            avgPastCallsPerHour = avgPastCalls / 24
            avgCurrentCallsPerHour = currentCalls / int(currentHour)

            avgPastPostTime = round(statistics.mean(pastPostTime))
            avgPastPostTimePerHour = avgPastPostTime / 24
            avgCurrentPostTimePerHour = currentPostTime / int(currentHour)

            avgPastOnCallTime = round(statistics.mean(pastOnCallTime))
            avgPastOnCallTimePerHour = avgPastOnCallTime / 24
            avgCurrentOnCallTimePerHour = currentOnCallTime / int(currentHour)

            avgPastDriveTime = round(statistics.mean(pastDriveTime))
            avgPastDriveTimePerHour = avgPastDriveTime / 24
            avgCurrentDriveTimePerHour = currentDriveTime / int(currentHour)

            avgPastUnits = round(statistics.mean(pastUnits))
            avgPastUnitsPerHour = avgPastUnits / 24
            avgCurrentUnitsPerHour = currentUnits / int(currentHour)

            avgPastPastEOS = round(statistics.mean(pastPastEOS))
            avgPastPastEOSPerHour = avgPastPastEOS / 24
            avgCurrentPastEOSPerHour = currentPastEOS / int(currentHour)

            avgPastLateCalls = round(statistics.mean(pastLateCalls))
            avgPastLateCallsPerHour = avgPastLateCalls / 24
            avgCurrentLateCallsPerHour = currentLateCalls / int(currentHour)

            avgPastLevelZero = round(statistics.mean(pastLevelZero))
            avgPastLevelZeroPerHour = avgPastLevelZero / 24
            avgCurrentLevelZeroPerHour = currentLevelZero / int(currentHour)

            if avgCurrentCallsPerHour > avgPastCallsPerHour:
                callStatus = "Above Average"
            elif avgCurrentCallsPerHour == avgPastCallsPerHour:
                callStatus = "Average"
            else:
                callStatus = "Below Average"

            if avgCurrentPostTimePerHour > avgPastPostTimePerHour:
                postTimeStatus = "Above Average"
            elif avgCurrentPostTimePerHour == avgPastPostTimePerHour:
                postTimeStatus = "Average"
            else:
                postTimeStatus = "Below Average"

            if avgCurrentOnCallTimePerHour > avgPastOnCallTimePerHour:
                onCallStatus = "Above Average"
            elif avgCurrentOnCallTimePerHour == avgPastOnCallTimePerHour:
                onCallStatus = "Average"
            else:
                onCallStatus = "Below Average"

            if avgCurrentDriveTimePerHour > avgPastDriveTimePerHour:
                driveTimeStatus = "Above Average"
            elif avgCurrentDriveTimePerHour == avgPastDriveTimePerHour:
                driveTimeStatus = "Average"
            else:
                driveTimeStatus = "Below Average"

            if avgCurrentUnitsPerHour > avgPastUnitsPerHour:
                unitStatus = "Above Average"
            if avgCurrentUnitsPerHour == avgPastUnitsPerHour:
                unitStatus = "Average"
            else:
                unitStatus = "Below Average"

            if avgCurrentPastEOSPerHour > avgPastPastEOSPerHour:
                pastEOSStatus = "Above Average"
            elif avgCurrentPastEOSPerHour == avgPastPastEOSPerHour:
                pastEOSStatus = "Average"
            else:
                pastEOSStatus = "Below Average"

            if avgCurrentLateCallsPerHour > avgPastLateCallsPerHour:
                lateCallStatus = "Above Average"
            elif avgCurrentLateCallsPerHour == avgPastLateCallsPerHour:
                lateCallStatus = "Average"
            else:
                lateCallStatus = "Below Average"

            if avgCurrentLevelZeroPerHour > avgPastLevelZeroPerHour:
                levelZeroStatus = "Above Average"
            elif avgCurrentLevelZeroPerHour == avgPastLevelZeroPerHour:
                levelZeroStatus = "Average"
            else:
                levelZeroStatus = "Below Average"

            self.system.update_one({"date" : current_dateTime("Date")},
                            {"$set": 
                            {"call_status" : callStatus,
                            "on_call_status" : onCallStatus,
                            "post_time_status" : postTimeStatus,
                            "drive_time_status" : driveTimeStatus,
                            "unit_status" : unitStatus,
                            "past_eos_status" : pastEOSStatus,
                            "late_call_status" : lateCallStatus,
                            "level_zero_status" : levelZeroStatus}
                            }, 
                            upsert=False)