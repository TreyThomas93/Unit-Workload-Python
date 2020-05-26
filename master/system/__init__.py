from assets.currentDatetime import current_dateTime
from assets.notifyLog import NotifyLog
from assets.errorHandler import checkError
from assets.errorHandler import error

import threading
import statistics
import datetime

class systemHandler():

    def __init__(self, system, liveWorkload, historicWorkload, hourlyCounts):
        self.system = system
        self.liveWorkload = liveWorkload
        self.historicWorkload = historicWorkload
        self.hourlyCounts = hourlyCounts
        self.notifyLog = NotifyLog(system, liveWorkload)
        self.alreadySent = False

        if current_dateTime("Time")[0:2] < str(12):
            self.flux = "before_noon"
        else:
            self.flux = "after_noon"

    @checkError
    def __call__(self, csvData, flux):

        self.flux = flux
        self.csvData = csvData

        obj = {
            "date" : current_dateTime("Date"), 
            "before_noon" : {
                "valid" : True,
                "accumulated" : {
                    "units" : 0,
                    "calls" : 0,
                    "post_time" : 0,
                    "on_call_time" : 0,
                    "drive_time" : 0,
                    "late_calls" : 0,
                    "past_eos" : 0,
                    "level_zero" : 0
                },
                "hourlyAverages" : {
                    "unit" : [],
                    "call" : [],
                    "on_call_time" : [],
                    "post_time" : [],
                    "drive_time" : [],
                },
                "logs" : []
            },
            "after_noon" : {
                "valid" : True,
                "accumulated" : {
                    "units" : 0,
                    "calls" : 0,
                    "post_time" : 0,
                    "on_call_time" : 0,
                    "drive_time" : 0,
                    "late_calls" : 0,
                    "past_eos" : 0,
                    "level_zero" : 0
                },
                "hourlyAverages" : {
                    "unit" : [],
                    "call" : [],
                    "on_call_time" : [],
                    "post_time" : [],
                    "drive_time" : [],
                },
                "logs" : []
            }
        }

        systemFound = self.system.find_one({ "date" : current_dateTime("Date") })
        
        if not systemFound:
            rollOver = self.liveWorkload.count_documents({})
            obj[self.flux]["accumulated"]["units"] = rollOver
            self.system.insert_one(obj)
            
            t1 = threading.Thread(target=self.getHourlyAverageCount("unit"))
            t2 = threading.Thread(target=self.getHourlyAverageCount("call"))
            t3 = threading.Thread(target=self.getHourlyAverageCount("on_call_time"))
            t4 = threading.Thread(target=self.getHourlyAverageCount("post_time"))
            t5 = threading.Thread(target=self.getHourlyAverageCount("drive_time"))

            t1.start()
            t2.start()
            t3.start()
            t4.start()
            t5.start()

            t1.join()
            t2.join()
            t3.join()
            t4.join()
            t5.join()

        hourlyCountFound = self.hourlyCounts.find_one({"date" : current_dateTime("Date")})

        # If it doesnt exist, insert it
        if not hourlyCountFound:
            self.hourlyCounts.insert_one({
                "date" : current_dateTime("Date"),
                "unitHours" : [],
                "callHours" : [],
                "on_call_timeHours" : [],
                "post_timeHours" : [],
                "drive_timeHours" : [],
            })

        t6 = threading.Thread(target=self.accumulateLevelZero)
        t7 = threading.Thread(target=self.getWeeklyOffOnTime)

        t8 = threading.Thread(target=self.getHourlyCount, args=("unit",))
        t9 = threading.Thread(target=self.getHourlyCount, args=("call",))
        t10 = threading.Thread(target=self.getHourlyCount, args=("on_call_time",))
        t11 = threading.Thread(target=self.getHourlyCount, args=("post_time",))
        t12 = threading.Thread(target=self.getHourlyCount, args=("drive_time",))

        t6.start()
        t7.start()
        t8.start()
        t9.start()
        t10.start()
        t11.start()
        t12.start()

        t6.join()
        t7.join()
        t8.join()
        t9.join()
        t10.join()
        t11.join()
        t12.join()

    @checkError
    def accumulateToSystem(self, key):
        print(f"{self.flux}.accumulated.{key}")
        self.system.update_one({"date" : current_dateTime("Date")},
        {"$inc": {f"{self.flux}.accumulated.{key}" : 1}}, upsert=False)

    @checkError
    def accumulateLevelZero(self):
        
        levelZero = [i["unit"] for i in self.csvData if i["status"] == "Driving" or i["status"] == "Posting" or i["status"] == "SOS"]

        if len(levelZero) > 0:
            if not self.alreadySent:
                msg = "System is Level Zero"
                self.notifyLog(msg, self.flux, notify=False)
                self.alreadySent = True
            
            self.system.update_one({"date" : current_dateTime("Date")}, {"$inc": {f"{self.flux}.accumulated.level_zero" : 1}}, upsert=False)
        else:
            self.alreadySent = False

    @checkError
    def getWeeklyOffOnTime(self):
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
                    error("getWeeklyOffOnTime", e)

        offOnTime = 100 - round((PastEOS / totalCrews) * 100) 

        dateRange = f"{dates[0]} - {current_dateTime('Date')}"    

        self.system.update_one({"date" : current_dateTime("Date")}, {
            "$set" : {"weekly_off_on_time" : {
                "daterange" : dateRange,
                "percentage" : offOnTime
            }}
        }, upsert=False) 

    @checkError
    def getHourlyCount(self, countFor):

        hourlyCount = self.hourlyCounts.find_one({"date" : current_dateTime("Date")})

        cT = current_dateTime("Time").split(":")[0]

        hoursArray = hourlyCount[f"{countFor}Hours"]

        system = self.system.find_one({"date" : current_dateTime("Date")})

        if countFor == "unit":
            count = self.liveWorkload.find({}).count()
        elif countFor == "call":
            count = system[self.flux]["accumulated"]["calls"]
        elif countFor == "on_call_time":
            count = system[self.flux]["accumulated"]["on_call_time"]
        elif countFor == "post_time":
            count = system[self.flux]["accumulated"]["post_time"]
        elif countFor == "drive_time":
            count = system[self.flux]["accumulated"]["drive_time"]

        if len(hoursArray) > 0:
            if not any(i['time'] == f"{cT}:00" for i in hoursArray):
                self.hourlyCounts.update_one({"date" : current_dateTime("Date")}, {
                    "$push" : { f"{countFor}Hours" : { "time" : f"{cT}:00", 
                    f"{countFor}Count" : count } }
                })
        else:
            self.hourlyCounts.update_one({"date" : current_dateTime("Date")}, {
                    "$push" : { f"{countFor}Hours" : { "time" : f"{cT}:00", 
                    f"{countFor}Count" : count } }
                })
        
    @checkError
    def getHourlyAverageCount(self, countFor):

        allHourlyCounts = self.hourlyCounts.find({})

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
        for item in allHourlyCounts:
            for i in item[f"{countFor}Hours"]:
                for hour in hours:
                    for k,v in hour.items():
                        if k == i["time"] and item["date"]:
                            v.append(i[f"{countFor}Count"])

        averageList = []
                    
        # Get mean of each list in hours
        for hour in hours:
            for k,v in hour.items():
                if len(v) > 0:
                    averageList.append({ k : statistics.mean(v)})
                else:
                    averageList.append({ k : 0 })

        self.system.update_one({"date" : current_dateTime("Date")}, {
            "$set" : { f"{self.flux}.hourlyAverages.{countFor}" : averageList }
        }, upsert=True)

    