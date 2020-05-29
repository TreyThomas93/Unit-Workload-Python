from assets.errorHandler import checkError
from assets.currentDatetime import current_dateTime
from datetime import datetime
from pprint import pprint
import statistics
from termcolor import colored

class liveWorkloadHandler():
    
    def __init__(self, liveWorkload, historicWorkload, system):
        self.max_threshold = 1
        self.max_task = 70
        self.notificationList = []
        self.liveWorkload = liveWorkload
        self.historicWorkload = historicWorkload
        self.system = system
        
    @checkError    
    def __call__(self, csvData):
        self.csvData = csvData

        self.unitWorkload()
        self.unitStatus()
        self.unitAverage()
        self.commitLiveWorkload()

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
            sos = unit["sos"]
            status = unit["status"]
            workload = unit["workload"]
            threshold = unit["threshold"]
            above_max = unit["above_max"]
            above_current = unit["above_current"]
            late_call = unit["late_call"]
            past_eos = unit["past_eos"]
            time_on_shift = unit["time_on_shift"]

            drive_time = unit["drive_time"]
            last_drive_time = unit["last_drive_time"]

            task_time = unit["task_time"]
            last_task_time = unit["last_task_time"]

            post_time = unit["post_time"]
            last_post_time = unit["last_post_time"]
            last_post = unit["last_post"]

            arrivals = unit["arrivals"]
            last_arrivals = unit["last_arrivals"]

            post_assignments = unit["post_assignments"]
            last_post_assignments = unit["last_post_assignments"]

            if threshold < self.max_threshold:

                if task_time > last_task_time:
                    if status == "Fueling" or status == "EOS" or status == "Late Call":
                        status = "Late Call"
                    else:
                        status = "On Call"
                    task_difference = (task_time - last_task_time)
                    self.system.accumulateToSystem("on_call_time", task_difference)
                elif post_time > last_post_time:
                    if threshold < 0.92:
                        status = "Posting"
                        post_difference = (post_time - last_post_time)
                        self.system.accumulateToSystem("post_time", post_difference)
                    elif threshold >= 0.92 and threshold < 0.94:
                        status = "Fueling"
                    elif threshold >= 0.94 and threshold < self.max_threshold:
                        status = "EOS"

                    unit["last_post"] = current_dateTime("Time")[0:5]
                else:
                    if threshold < 0.92:
                        drive_time = (time_on_shift - (task_time + post_time))
                        
                        status = "Driving"

                        drive_time_difference = (drive_time - last_drive_time)

                        unit["drive_time"]+=drive_time_difference

                        self.system.accumulateToSystem("drive_time", drive_time_difference)

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

            if unit["workload"] >= self.max_threshold:
                unit["above_max"] = True
                unit["above_current"] = True
                if not above_max:
                    msg = f"Unit {unit['unit']} Above Max Threshold"
                    self.notificationList.append(msg)
            elif unit["workload"] < self.max_threshold and unit["workload"] > unit["threshold"]:
                unit["above_current"] = True
                unit["above_max"] = False
            elif unit["workload"] <= unit["threshold"]:
                unit["above_current"] = False
                unit["above_max"] = False

            if status == "Late Call" and not late_call:
                unit["late_call"] = True
                msg = f"Unit {unit['unit']} Received Late Call"
                self.notificationList.append(msg)
                self.system.accumulateToSystem("late_call", 1)

            if status == "Past EOS" and not past_eos:
                unit["past_eos"] = True
                msg = f"Unit {unit['unit']} Past EOS"
                self.notificationList.append(msg)
                self.system.accumulateToSystem("past_eos", 1)
            
            unit["status"] = status

            if arrivals > last_arrivals:
                arrivals_difference = (arrivals - last_arrivals)
                self.system.accumulateToSystem("calls", arrivals_difference)

            if post_assignments > last_post_assignments:
                post_assignments_difference = (post_assignments - last_post_assignments)
                self.system.accumulateToSystem("post_assignments", post_assignments_difference)

            del unit["last_task_time"]
            del unit["last_post_time"]
            del unit["last_drive_time"]
            del unit["last_post_assignments"]
            del unit["last_arrivals"]

    @checkError
    def unitAverage(self):
        values = []
        for unit in self.csvData:
            shiftAverage = self.historicWorkload.find({ "sos" : unit["sos"] })

            if shiftAverage:
                for average in shiftAverage:
                    values.append(average["workload"])

        
            if len(values) > 0:
                average = round(statistics.mean(values), 2)
            else:
                average = 0

            unit["shift_average"] = average

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

                type = "New"

            print(colored(f"--> Unit {unit['unit']} - Type: {type}", "yellow"))
