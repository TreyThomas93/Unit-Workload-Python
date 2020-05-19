from assets.errorHandler import checkError
from assets.currentDatetime import current_dateTime

class historicWorkloadHandler():

    def __init__(self, liveWorkload, shiftAverage, historicWorkload):
        self.liveWorkload = liveWorkload
        self.shiftAverage = shiftAverage
        self.historicWorkload = historicWorkload

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

                print(f"Unit {unit} Purged - Last Updated: {updated_at}")
                
                if threshold > 0.92:
                    # SAVE TO SHIFT AVERAGE 
                    
                    avg = {
                        "sos" : sos,
                        "workload" : workload
                    }

                    self.shiftAverage.insert_one(avg)

                    print(f"Unit {unit} Added To Shift Average Database")

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

                    print(f"Unit {unit} Added To Historic Workload Database")
                    print("================================================")

                #  DELETE FROM LIVE WORKLOAD 
                self.liveWorkload.delete_one({"unit" : unit})
    