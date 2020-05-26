from assets.database import mongoDatabase
from assets.currentDatetime import current_dateTime
from assets.errorHandler import checkError
from assets.notifyLog import NotifyLog

from workload.live import liveWorkloadHandler
from workload.historic import historicWorkloadHandler
from system import systemHandler

from csvHandler import CSV

import platform
import os
import time
from pprint import pprint
import threading
from termcolor import colored

class Master():

    def __init__(self):
        self.testing = True

        if not self.testing:
            if platform.system() == "Windows":
                self.path_to_csv_file = "C:/Users/TreyT/Downloads/Live Workload Report.csv"
            elif platform.system() == "Linux":
                self.path_to_csv_file = "/home/pi/Downloads/Live Workload Report.csv"
        else:
            self.path_to_csv_file = f"{os.getcwd()}/csvTestFile.csv"

        self.cycle = 0
        self.iterationCount = 0

        self.mongo = mongoDatabase()
        self.liveWorkload = self.mongo.liveWorkload
        self.historicWorkload = self.mongo.historicWorkload
        self.system = self.mongo.system
        self.hourlyCounts = self.mongo.hourlyCounts
        self.master = self.mongo.master

        self.systemHandler = systemHandler(self.system, self.liveWorkload, self.historicWorkload, self.hourlyCounts)

        self.notifyLog = NotifyLog(self.system, self.liveWorkload)

        self.csv = CSV(self.path_to_csv_file, self.liveWorkload)

        self.liveWorkloadHandler = liveWorkloadHandler(self.liveWorkload, self.historicWorkload, self.systemHandler)

        self.historicWorkloadHandler = historicWorkloadHandler(
            self.liveWorkload, self.historicWorkload)

    def __call__(self):
        if current_dateTime("Time")[0:2] < str(12):
            self.flux = "before_noon"
        else:
            self.flux = "after_noon"

    @checkError
    def listen(self):
        if os.path.exists(self.path_to_csv_file):
            start = time.perf_counter()
            print(colored("~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "blue"))
            print(colored("\n[CSV FILE FOUND]", "green"))
            print(colored("~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "blue"))
            self.csv.csvFile()
            csvData = self.csv.csvData

            print(colored("\n[HANDLING LIVE WORKLOAD]", "green"))
            print(colored("~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "blue"))
            self.liveWorkloadHandler(csvData)

            print(colored("\n[NOTIFY/LOG]", "green"))
            print(colored("~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "blue"))
            self.notifyLog(self.liveWorkloadHandler.notificationList, self.flux)

            print(colored("\n[HANDLING HISTORIC WORKLOAD]", "green"))
            print(colored("~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "blue"))
            self.historicWorkloadHandler(csvData)

            print(colored("\n[HANDLING SYSTEM]", "green"))
            print(colored("~~~~~~~~~~~~~~~~~~~~~~~~~~~~", "blue"))
            self.systemHandler(csvData, self.flux)

            self.iterationCount = 0
            self.cycle += 1
            self.csv.csvData.clear()
            self.liveWorkloadHandler.notificationList.clear()

            if not self.testing:
                os.remove(self.path_to_csv_file)

            end = time.perf_counter()

            print(colored(
                f"\nCycle {self.cycle} Complete - {current_dateTime()} - Took {round(end-start, 2)} second(s)\n", "yellow"))

        self.iterationCount += 1
        if self.iterationCount == 1:  # 2 minutes without CSV will send notification
            msg = "[ALERT] - CSV Undetected For 2 Minutes"
            self.notifyLog(msg, self.flux, log=False)
            self.master.insert_one({ 
                "dateTime" : current_dateTime(),
                "message" : msg
                 })

        if self.iterationCount == 1800:  # 30 minutes then place system data invalid
            self.system.update_one({"date": current_dateTime("Date")},
                                   {"$set": {f"{self.flux}.valid": False}}, upsert=False)
            print("[SYSTEM DATA] - Invalid")

if __name__ == "__main__":
    master = Master()
    while True:
        master()
        master.listen()
        time.sleep(1)
        break
