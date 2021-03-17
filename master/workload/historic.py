from assets.errorHandler import checkError
from assets.currentDatetime import current_dateTime

import threading
from termcolor import colored

class historicWorkloadHandler():

    def __init__(self, liveWorkload, historicWorkload):
        self.liveWorkload = liveWorkload
        self.historicWorkload = historicWorkload

    @checkError
    def __call__(self, csvData):
        t1 = threading.Thread(target=self.checkOutdated, args=(csvData,))
        t1.start()
        t1.join()

    @checkError
    def checkOutdated(self, csvData):
        checkOutdatedList = [ unit["unit"] for unit in csvData ]
        for row in self.liveWorkload.find():
            unit = row["unit"]
            updated_at = row["updated_at"]
            sos = row["sos"]
            workload = row["workload"]
            threshold = row["threshold"]
            crew_member_one = row["crew_member_one"]
            crew_member_two = row["crew_member_two"]
            task_time = row["task_time"]
            arrivals = row["arrivals"]
            post_time = row["post_time"]
            late_call = row["late_call"]
            past_eos = row["past_eos"]

            # Check For Outdated Unit Data If Unit not in new CSV file data
            if unit not in checkOutdatedList:

                print(colored(f"Unit {unit} Purged - Last Updated: {updated_at}", "yellow"))
                
                if threshold > 0.92:
                    # SAVE TO HISTORIC WORKLOAD 
                    historic = {
                        "date" : current_dateTime("Date"),
                        "crew_member_one" : crew_member_one,
                        "crew_member_two" : crew_member_two,
                        "unit" : unit,
                        "sos" : sos,
                        "task_time" : task_time,
                        "arrivals" : arrivals,
                        "post_time" : post_time,
                        "workload" : workload,
                        "late_call" : late_call,
                        "past_eos" : past_eos
                    }

                    self.historicWorkload.insert_one(historic)

                    print(colored(f"Unit {unit} Added To Historic Workload Database", "yellow"))
                    print(colored("================================================", "blue"))

                #  DELETE FROM LIVE WORKLOAD 
                self.liveWorkload.delete_one({"unit" : unit})
    