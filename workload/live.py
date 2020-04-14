from assets.errorHandler import checkError
from assets.currentDatetime import current_dateTime
from datetime import datetime
from pprint import pprint

class liveWorkloadHandler():
    
    def __init__(self, systemHandler):
        self.max_threshold = 1
        self.max_task = 70
        self.notificationList = []
        self.system = systemHandler
        self.liveWorkload = self.system.liveWorkload
        
    def __call__(self, csvData):
        self.csvData = csvData

    @checkError
    def unitWorkload(self):
        for unit in self.csvData:
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
            current_threshold = (self.max_threshold / 12) * round(float(hours_diff), 2)
            
            # Check If Arrivals Above Zero 
            if arrivals > 0:
                # Set Max Task and Get Task Differential 
                true_task = (task_time / arrivals)
                task_dif = self.max_task + true_task

                # Workload Formula 
                workload = round(((percentage_worked / task_dif) * 100) + (arrivals / 10), 2)
                workload = workload - (post_time / 100)
                
            # If Arrivals Not More Than Zero, Workload = Current Threshold 
            else:
                workload = ( current_threshold - (post_time / 100))
                
            unit["workload"] = round(workload, 2)
            unit["threshold"] = round(current_threshold, 2)
            unit["ratio"] = (round(workload, 2) - round(current_threshold, 2))

    @checkError 
    def unitStatus(self):
        for unit in self.csvData:
            status = unit["status"]
            workload = unit["workload"]
            threshold = unit["threshold"]
            above_max = unit["above_max"]
            late_call = unit["late_call"]
            past_eos = unit["past_eos"]
            task_time = unit["task_time"]
            last_task_time = unit["last_task_time"]
            drive_time = unit["drive_time"]
            on_call_time = unit["on_call_time"]
            post_time = unit["post_time"]
            last_post_time = unit["last_post_time"]
            last_post = unit["last_post"]
            arrivals = unit["arrivals"]
            last_arrivals = unit["last_arrivals"]

            if threshold < self.max_threshold:
                
                if task_time > last_task_time:
                    if status == "Fueling" or status == "EOS" or status == "Late Call":
                        status = "Late Call"
                    else:
                        status = "On Call"
                    unit["on_call_time"]+=1
                    self.system.accumulatedOnCallTime()

                elif post_time > last_post_time:
                    if threshold < 0.92:
                        status = "Posting"
                        self.system.accumulatedPostTime()
                    elif threshold >= 0.92 and threshold < 0.94:
                        status = "Fueling"
                    elif threshold >= 0.94 and threshold < self.max_threshold:
                        status = "EOS"

                    unit["last_post"] = current_dateTime("Time")[0:5]

                else:
                    if threshold < 0.92:
                        status = "Driving"
                        unit["drive_time"]+=1
                        self.system.accumulatedDriveTime()
                    elif threshold >= 0.92 and threshold < 0.94:
                        status = "Fueling"
                    elif threshold >= 0.94 and threshold < self.max_threshold:
                        status = "EOS"
                    unit["late_call"] = False

            else:
                status = "Past EOS"

            if threshold >= 1.5:
                status = "SOS"
                unit["workload"] = 0
                unit["threshold"] = 0

            if workload >= self.max_threshold and not above_max:
                unit["above_max"] = True
                msg = f"Unit {unit['unit']} Above Max Threshold"
                self.notificationList.append(msg)

            if status == "Late Call" and not late_call:
                unit["late_call"] = True
                msg = f"Unit {unit['unit']} Received Late Call"
                self.notificationList.append(msg)
                self.system.accumulatedLateCalls()

            if status == "Past EOS" and not past_eos:
                unit["past_eos"] = True
                msg = f"Unit {unit['unit']} Past EOS"
                self.notificationList.append(msg)
                self.system.accumulatedPastEOS()
            
            unit["status"] = status

            if arrivals > last_arrivals:
                self.system.accumulatedCalls()

    @checkError
    def commitLiveWorkload(self):
        for unit in self.csvData:
            unitExists = self.liveWorkload.find_one({"unit" : unit["unit"]})
            if unitExists:
                self.liveWorkload.update_one({"unit" : unit["unit"]}, 
                {"$set": unit}, upsert=True)

                type = "Existing"
            else:
                self.liveWorkload.insert_one(unit)

                self.system.accumulatedUnits()

                type = "New"

            print(f"Unit {unit['unit']} - Type: {type}")
