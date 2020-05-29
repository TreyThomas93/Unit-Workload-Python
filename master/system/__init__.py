from assets.currentDatetime import current_dateTime
from assets.notifyLog import NotifyLog
from assets.errorHandler import checkError
from assets.errorHandler import error

import threading
import statistics
import datetime
from pprint import pprint

class systemHandler():

    def __init__(self, system, liveWorkload, historicWorkload):
        self.system = system
        self.liveWorkload = liveWorkload
        self.historicWorkload = historicWorkload
        self.notifyLog = NotifyLog(system, liveWorkload)
        self.alreadySent = False

    @checkError
    def __call__(self, csvData):

        
        self.csvData = csvData

        obj = {
            "date" : current_dateTime("Date"), 
            "valid" : True,
            "accumulated" : {
                "units" : 0,
                "calls" : 0,
                "post_time" : 0,
                "on_call_time" : 0,
                "drive_time" : 0,
                "late_calls" : 0,
                "past_eos" : 0,
                "level_zero" : 0,
                "post_assignments" : 0
            },
            "hourly" : {
                "unit" : [],
                "call" : [],
                "on_call_time" : [],
                "post_time" : [],
                "drive_time" : [],
                "task_time" : [],
                "post_assignments" : []
            },
            "logs" : []
        }

        systemFound = self.system.find_one({ "date" : current_dateTime("Date") })
        
        if not systemFound:
            rollOver = self.liveWorkload.count_documents({})
            obj["accumulated"]["units"] = rollOver
            self.system.insert_one(obj)
            
            t1 = threading.Thread(target=self.getHourlyAverageCount("unit"))
            t2 = threading.Thread(target=self.getHourlyAverageCount("call"))
            t3 = threading.Thread(target=self.getHourlyAverageCount("on_call_time"))
            t4 = threading.Thread(target=self.getHourlyAverageCount("post_time"))
            t5 = threading.Thread(target=self.getHourlyAverageCount("drive_time"))
            t6 = threading.Thread(target=self.getHourlyAverageCount("task_time"))
            t7 = threading.Thread(target=self.getHourlyAverageCount("post_assignments"))

            t1.start()
            t2.start()
            t3.start()
            t4.start()
            t5.start()
            t6.start()
            t7.start()

            t1.join()
            t2.join()
            t3.join()
            t4.join()
            t5.join()
            t6.join()
            t7.join()

        t8 = threading.Thread(target=self.accumulateLevelZero)
        t9 = threading.Thread(target=self.getWeeklyOffOnTime)

        t10 = threading.Thread(target=self.getHourlyCount, args=("unit",))
        t11 = threading.Thread(target=self.getHourlyCount, args=("call",))
        t12 = threading.Thread(target=self.getHourlyCount, args=("on_call_time",))
        t13 = threading.Thread(target=self.getHourlyCount, args=("post_time",))
        t14 = threading.Thread(target=self.getHourlyCount, args=("drive_time",))
        t15 = threading.Thread(target=self.getHourlyCount, args=("task_time",))
        t16 = threading.Thread(target=self.getHourlyCount, args=("post_assignments",))

        t8.start()
        t9.start()
        t10.start()
        t11.start()
        t12.start()
        t13.start()
        t14.start()
        t15.start()
        t16.start()

        t8.join()
        t9.join()
        t10.join()
        t11.join()
        t12.join()
        t13.join()
        t14.join()
        t15.join()
        t16.join()

    @checkError
    def accumulateToSystem(self, key, increment):
        if increment != None and increment != 0:
            self.system.update_one({"date" : current_dateTime("Date")},
            {"$inc": {f"accumulated.{key}" : increment}}, upsert=False)

    @checkError
    def accumulateLevelZero(self):
        
        levelZero = [i["unit"] for i in self.csvData if i["status"] == "Driving" or i["status"] == "Posting" or i["status"] == "SOS"]

        if len(levelZero) == 0:
            if not self.alreadySent:
                msg = "System is Level Zero"
                self.notifyLog(msg, notify=False)
                self.alreadySent = True
            
            self.system.update_one({"date" : current_dateTime("Date")}, {"$inc": {"accumulated.level_zero" : 1}}, upsert=False)
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

        totalHistoric = self.historicWorkload.count_documents({})

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

        if totalCrews > 0:
            offOnTime = 100 - round((PastEOS / totalCrews) * 100) 
        else:
            offOnTime = 100

        dateRange = f"{dates[0]} - {current_dateTime('Date')}"    

        self.system.update_one({"date" : current_dateTime("Date")}, {
            "$set" : {"weekly_off_on_time" : {
                "daterange" : dateRange,
                "percentage" : offOnTime
            }}
        }, upsert=False) 

    @checkError
    def getHourlyCount(self, countFor):

        system = self.system.find_one({"date" : current_dateTime("Date")})

        cT = current_dateTime("Time").split(":")[0]
       
        hoursToday = system["hourly"][countFor]

        if countFor == "unit":
            count = self.liveWorkload.find({}).count()
        elif countFor == "call":
            count = system["accumulated"]["calls"]
        elif countFor == "on_call_time":
            count = system["accumulated"]["on_call_time"]
        elif countFor == "post_time":
            count = system["accumulated"]["post_time"]
        elif countFor == "drive_time":
            count = system["accumulated"]["drive_time"]
        elif countFor == "task_time":
            onCallTime = system["accumulated"]["on_call_time"]
            calls = system["accumulated"]["calls"]

            if calls > 0:
                count = round(onCallTime / calls)
            else:
                count = 0
        elif countFor == "post_assignments":
            count = system["accumulated"]["post_assignments"]

        for i in hoursToday:
            if i["time"] == f"{cT}:00":
                average = i["average"]
                if i["today"] == None:
                    self.system.update_one({
                        "date" : current_dateTime("Date"),
                        f"hourly.{countFor}.time" : f"{cT}:00"
                    }, {
                        "$set" : { f"hourly.{countFor}.$" : {
                            "time" : f"{cT}:00",
                            "today" : count,
                            "average" : average
                        } }
                    })
        
    @checkError
    def getHourlyAverageCount(self, countFor):

        allHourlyCounts = self.system.find({})

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

        for item in allHourlyCounts:
            if item["valid"]:
                if countFor in item["hourly"]:
                    for i in item["hourly"][countFor]:
                        time = i["time"]
                        today = i["today"]

                        for hour in hours:
                            for k,v in hour.items():
                                if time == k:
                                    if today != None:
                                        v.append(today)

        averageList = []
        # Get mean of each list in hours
        for hour in hours:
            for k,v in hour.items():
                if len(v) > 0:
                    averageList.append({"time" : k, "today" : None, "average" : statistics.mean(v)})
                else:
                    averageList.append({"time" : k, "today" : None, "average" : 0})

        self.system.update_one({"date" : current_dateTime("Date")}, {
            "$set" : { f"hourly.{countFor}" : averageList }
        }, upsert=True)

        averageList.clear()

    