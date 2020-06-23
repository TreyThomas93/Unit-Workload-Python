from assets.errorHandler import checkError
from assets.currentDatetime import current_dateTime
from datetime import datetime
from pprint import pprint
import statistics
from termcolor import colored
from random import randint


class liveWorkloadHandler():

    def __init__(self, liveWorkload, system):
        self.max_threshold = 1
        self.max_task = 70
        self.liveWorkload = liveWorkload
        self.system = system

        self.cycleNumber = 0
        self.makeLevelZero = False

    @checkError
    def __call__(self, Data):
        self.Data = Data

        print("DROPPED SYSTEM")
        self.system.drop()

        self.cycleNumber+=1

        if (self.cycleNumber % 5 == 0):
            self.makeLevelZero = True
        else:
            self.makeLevelZero = False

        self.unitWorkload()
        self.unitStatus()
        self.commitLiveWorkload()
        
        if self.makeLevelZero:
            self.levelZero()

    @checkError
    def levelZero(self):
        log = "System is Level Zero"
        self.Log(log)

    @checkError
    def snapShot(self):
        driving = self.liveWorkload.find({"status": "Driving"}).count()
        posting = self.liveWorkload.find({"status": "Posting"}).count()
        sos = self.liveWorkload.find({"status": "SOS"}).count()

        level = driving + posting + sos

        obj = {
            "driving": driving,
            "posting": posting,
            "level": level,
            "log": None
        }

        return obj

    @checkError
    def Log(self, toLog):

        systemFound = self.system.find_one({"date": "06/19/20"})

        if not systemFound:
            self.system.insert_one({
                "date": "06/19/20",
                "logs": []
            })

        obj = self.snapShot()

        obj["log"] = f"{toLog} - {current_dateTime('Time')}"

        self.system.update_one({"date": "06/19/20"},
                               {"$push": {"logs": obj}}, upsert=False)

    @checkError
    def unitWorkload(self):
        for unit in self.Data:
            sos = unit["sos"]
            arrivals = unit["arrivals"]
            task_time = unit["task_time"]
            post_time = unit["post_time"]

            # Get Time Difference Between SOS & Current Time
            current_time = current_dateTime("Time")
            s1 = sos
            s2 = str(current_time).split(" ")[-1]

            FMT = '%H:%M:%S'
            tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)
            tdelta = str(tdelta).split(" ")[-1]

            hours_diff = tdelta[:4]
            hours_diff = hours_diff.replace(":", ".")

            # Get Percentage Of Shift Currently Worked
            percentage_worked = round(float(hours_diff) / 12, 2)

            # Set Max Threshold and Determine Current Threshold
            current_threshold = (self.max_threshold / 12) * \
                round(float(hours_diff), 2)

            # Check If Arrivals Above Zero
            if arrivals > 0:
                # Set Max Task and Get Task Differential
                true_task = (task_time / arrivals)
                task_dif = self.max_task + true_task

                # Workload Formula
                workload = round(
                    ((percentage_worked / task_dif) * 100) + (arrivals / 10), 2)
                workload = workload - (post_time / 100)

            # If Arrivals Not More Than Zero, Workload = Current Threshold
            else:
                workload = (current_threshold - (post_time / 100))

            unit["workload"] = round(workload, 2)
            unit["threshold"] = round(current_threshold, 2)
            unit["ratio"] = (round(workload, 2) - round(current_threshold, 2))

    @checkError
    def unitStatus(self):
        unitStatus = [
            "On Call",
            "Posting",
            "Driving",
            "Fueling",
            "Late Call"
        ]

        for unit in self.Data:
            status = unit["status"]
            post_time = unit["post_time"]
            drive_time = unit["drive_time"]
            task_time = unit["task_time"]
            threshold = unit["threshold"]

            if threshold > 0.92 and threshold < 1:
                unit["status"] = unitStatus[randint(3, 4)]
            elif threshold >= 1:
                unit["status"] = "Past EOS"
            else:
                unit["status"] = unitStatus[randint(0, 2)]

            if unit["status"] == "Posting":
                unit["post_time"] += 1
            elif unit["status"] == "Drive Time":
                unit["drive_time"] += 1
            elif unit["status"] == "On Call":
                unit["task_time"] += 1

            if unit["status"] == "Late Call":
                log = f"Unit {unit['unit']} Received Late Call"
                self.Log(log)
            elif unit["status"] == "Past EOS":
                log = f"Unit {unit['unit']} Past EOS"
                self.Log(log)

            if unit["workload"] >= self.max_threshold:
                log = f"Unit {unit['unit']} Above Max Threshold"
                self.Log(log)

            if self.makeLevelZero:
                unit["status"] = "On Call"

    @checkError
    def purgeAll(self):
        print("DROPPED LIVE WORKLOAD")
        self.liveWorkload.drop()

    @checkError
    def commitLiveWorkload(self):
        self.purgeAll()
        for unit in self.Data:
            unitExists = self.liveWorkload.find_one({"unit": unit["unit"]})
            if unitExists:
                self.liveWorkload.update_one({"unit": unit["unit"]},
                                             {"$set": unit}, upsert=True)

                type = "Existing"
            else:
                self.liveWorkload.insert_one(unit)

                type = "New"

            print(colored(f"--> Unit {unit['unit']} - Type: {type}", "yellow"))
