from assets.currentDatetime import current_dateTime
from assets.errorHandler import checkError
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pprint import pprint
import statistics
from env import FROM_EMAIL, TO_EMAIL, PASSWORD
import datetime

class SystemHandler():

    def __init__(self, system, liveWorkload, historicWorkload, hourlyUnitAverage):
        self.system = system
        self.liveWorkload = liveWorkload
        self.historicWorkload = historicWorkload
        self.hourlyUnitAverage = hourlyUnitAverage
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
            "systemLog" : []
        }

        Found = self.system.find_one({"date" : current_dateTime("Date")})

        if not Found:
            rollOver = self.liveWorkload.count_documents({})
            foundObj["accumulated_units"] = rollOver
            self.system.insert_one(foundObj)

            # Get Unit Hour Averages
            self.getUnitHourAverage()

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
        
        server = smtplib.SMTP( "smtp.gmail.com", 587 )
        server.starttls()
        server.login(FROM_EMAIL, PASSWORD)
        
        dT = type(data)

        if dT == str:
            # server.sendmail( FROM_EMAIL, TO_EMAIL, data)
            msg = MIMEMultipart()  # create a message
            msg['From'] = FROM_EMAIL
            msg['To'] = TO_EMAIL
            msg['Subject'] = "[SYSTEM ALERT]"
            msg.attach(MIMEText(data, 'plain'))
            server.send_message(msg)
            del msg
            print(f"[MESSAGE SENT] {data}")
            
        elif dT == list:
            for message in data:
                # server.sendmail( FROM_EMAIL, TO_EMAIL, message)
                msg = MIMEMultipart()  # create a message
                msg['From'] = FROM_EMAIL
                msg['To'] = TO_EMAIL
                msg['Subject'] = "[SYSTEM ALERT]"
                msg.attach(MIMEText(message, 'plain'))
                server.send_message(msg)
                del msg
                print(f"[MESSAGE SENT] {message}")

        server.quit()

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

            self.system.update_one({"date" : current_dateTime("Date")},
                            {"$set": 
                            {
                            "call_average" : round(avgPastCallsPerHour * int(currentHour)),
                            
                            "on_call_average" : round(avgPastOnCallTimePerHour * int(currentHour)),
                            
                            "post_time_average" : round(avgPastPostTimePerHour * int(currentHour)),
                            
                            "drive_time_average" : round(avgPastDriveTimePerHour * int(currentHour)),
                            
                            "unit_average" : avgPastUnits,
                            
                            "past_eos_average" : round(avgPastPastEOSPerHour * int(currentHour)),
                            
                            "late_call_average" : round(avgPastLateCallsPerHour * int(currentHour)),
                          
                            "level_zero_average" : round(avgPastLevelZeroPerHour * int(currentHour))}
                            }, 
                            upsert=False)

    @checkError
    def offOnTimePercentage(self):
        # GET WEEKLY OFF ON TIME PERCENTAGE

        theday = datetime.date.today()
        weekday = theday.isoweekday()
        # The start of the week
        start = theday - datetime.timedelta(days=weekday)
        # build a simple range
        dates = [start + datetime.timedelta(days=d) for d in range(7)]

        dates = [datetime.datetime.strftime(d, "%m/%d/%y") for d in dates]

        historicWorkload = self.historicWorkload.find({})

        PastEOS = 0
        totalCrews = 0

        for data in historicWorkload:
            if data["date"] in dates:
                totalCrews+=1
                try:
                    if data["past_eos"] and data["late_call"]:
                        PastEOS+=1
                except Exception as e:
                    pass

        offOnTime = 100 - round((PastEOS / totalCrews) * 100) 

        dateRange = f"{dates[0]} - {current_dateTime('Date')}"      

        self.system.update_one({"date" : current_dateTime("Date")}, {
            "$set" : {"weeklyoffontime" : {
                "daterange" : dateRange,
                "offontimepercentage" : offOnTime
            }}
        }, upsert=False) 

    @checkError
    def HourlyUnitAverage(self):

        unitAverage = self.hourlyUnitAverage.find_one({"date" : current_dateTime("Date")})

        if not unitAverage:
            self.hourlyUnitAverage.insert_one({
                "date" : current_dateTime("Date"),
                "unitHours" : []
            })
        else:
            cT = current_dateTime("Time").split(":")[0]

            unitHours = unitAverage["unitHours"]

            unitCount = self.liveWorkload.find({}).count()

            if len(unitHours) > 0:
                if not any(i['time'] == f"{cT}:00" for i in unitHours):
                    self.hourlyUnitAverage.update_one({"date" : current_dateTime("Date")}, {
                        "$push" : { "unitHours" : { "time" : f"{cT}:00", 
                        "unitCount" : unitCount } }
                    })
            else:
                self.hourlyUnitAverage.update_one({"date" : current_dateTime("Date")}, {
                        "$push" : { "unitHours" : { "time" : f"{cT}:00", 
                        "unitCount" : unitCount } }
                    })

    @checkError
    def getUnitHourAverage(self):

        unitHours = self.hourlyUnitAverage.find({})

        hours = [
            { "00:00" : [] },
            { "01:00" : [] },
            { "02:00" : [] },
            { "03:00" : [] },
            { "04:00" : [] },
            { "05:00" : [] },
            { "06:00" : [] },
            { "07:00" : [] },
            { "08:00" : [] },
            { "09:00" : [] },
            { "10:00" : [] },
            { "11:00" : [] },
            { "12:00" : [] },
            { "13:00" : [] },
            { "14:00" : [] },
            { "15:00" : [] },
            { "16:00" : [] },
            { "17:00" : [] },
            { "18:00" : [] },
            { "19:00" : [] },
            { "20:00" : [] },
            { "21:00" : [] },
            { "22:00" : [] },
            { "23:00" : [] }
        ]

        # Add unit counts to appropriate lists in hours dict
        for item in unitHours:
            for i in item["unitHours"]:
                for hour in hours:
                    for k,v in hour.items():
                        if k == i["time"]:
                            v.append(i["unitCount"])

        averageList = []
                    
        # Get mean of each list in hours
        for hour in hours:
            for k,v in hour.items():
                if len(v) > 0:
                    averageList.append({ k : statistics.mean(v)})
                else:
                    averageList.append({ k : 0 })

        self.system.update_one({"date" : current_dateTime("Date")}, {
            "$set" : { "unitHourlyAverages" : averageList }
        }, upsert=True)

        