from assets.database import mongoDatabase
from workload.live import liveWorkloadHandler
from workload.historic import historicWorkloadHandler
import platform, os, time
from csvHandler import CSV
from pprint import pprint
from workload.system import SystemHandler
from assets.currentDatetime import current_dateTime
from assets.errorHandler import checkError

class Init():

    def __init__(self):
        if platform.system() == "Windows":
            self.path_to_csv_file = "C:/Users/TreyT/Downloads/Live Workload Report.csv"
        elif platform.system() == "Linux":
            self.path_to_csv_file = "/home/pi/Downloads/Live Workload Report.csv"

        self.cycle = 0
        self.iterationCount = 0

        self.mongo = mongoDatabase()
        self.liveWorkload = self.mongo.liveWorkload
        self.historicWorkload = self.mongo.historicWorkload
        self.shiftAverage = self.mongo.shiftAverage
        self.system = self.mongo.system
        self.systemHandler = SystemHandler(self.system, self.liveWorkload)

        self.csv = CSV(self.path_to_csv_file, self.liveWorkload)
        self.liveWorkloadHandler = liveWorkloadHandler(self.systemHandler)
        self.historicWorkloadHandler = historicWorkloadHandler(self.liveWorkload, self.shiftAverage, self.historicWorkload)

    @checkError 
    def listen(self):
        if os.path.exists(self.path_to_csv_file):
            print("[CSV FILE FOUND]\n")
            self.csv.csvFile()
            csvData = self.csv.csvData

            print("[HANDLING LIVE WORKLOAD]")
            self.systemHandler()
            self.liveWorkloadHandler(csvData)
            self.liveWorkloadHandler.unitWorkload()
            self.liveWorkloadHandler.unitStatus()
            self.liveWorkloadHandler.commitLiveWorkload()

            print("\n[HANDLING HISTORIC WORKLOAD]")
            self.historicWorkloadHandler.checkOutdated(csvData)

            notificationList = self.liveWorkloadHandler.notificationList
            if len(notificationList) > 0:
                print(f"[NOTIFY/LOG] - {len(notificationList)} EVENTS")
                self.systemHandler.Notify(notificationList)
                self.systemHandler.Log(notificationList)

            self.systemHandler.accumulatedLevelZero(csvData)

            self.systemHandler.averageStatus()

            self.iterationCount = 0
            self.cycle+=1
            self.csv.csvData.clear()
            notificationList.clear()

            print(f"\nCycle {self.cycle} Complete - {current_dateTime()}\n")
        
        self.iterationCount+=1
        if self.iterationCount == 120: # 2 minutes without CSV will send notification
            msg = "[ALERT] - CSV Undetected For 2 Minutes"
            self.systemHandler.Notify(msg)

        if self.iterationCount == 600: # 10 minutes then place system data invalid
            self.system.update_one({"date" : current_dateTime("Date")},
            {"$set" : {"valid" : False}}, upsert=False)
            print("[SYSTEM DATA] - Invalid")

if __name__ == "__main__":
    init = Init()
    while True:
        init.listen()
        time.sleep(1)

