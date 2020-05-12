import csv, os
from assets.currentDatetime import current_dateTime
from assets.errorHandler import checkError

class CSV():

    def __init__(self, path, liveWorkload):
        self.path = path
        self.csvData = []
        self.liveWorkload = liveWorkload

    @checkError
    def convert_to_minutes(self, val):
        frm = val.split(":")
        h = int(frm[0]) * 60
        m = int(frm[1])
        return h + m

    @checkError
    def check_for_jump(self, unit, arrivals, task_time):
        found = self.liveWorkload.find_one({ "unit": unit })
        if found:
            if arrivals > 0:
                if arrivals == (found["arrivals"] * 2):
                    arrivals = round(arrivals / 2)
                elif (task_time / arrivals) < 40:
                    arrivals = round(arrivals / 2)
                else:
                    arrivals = arrivals
        return arrivals

    @checkError
    def csvFile(self):
        current_time = current_dateTime("Time")

        with open(self.path, newline="") as file:
            reader = csv.reader(file)
            header = next(reader)

            filter_by_list = ['Unit', 'UnitStartTime', 'ActualTaskTimeUHU',
                                'Arrivals', 'Textbox8', 'Crew', "PostAssignments"]

            ## Get index of param in csv list ##
            filter_by_list_index = [header.index(i) for i in filter_by_list]

            checkDuplicates = []
            divisions = ["Eastern Division"]

            for row in reader:
                if row and row[0] in divisions:
                    unit = row[filter_by_list_index[0]]
                    if unit not in checkDuplicates:
                        checkDuplicates.append(unit)
                        
                        sos = row[filter_by_list_index[1]]
                        
                        task_time = self.convert_to_minutes(row[filter_by_list_index[2]])
                        
                        task_time = abs(task_time)
                        
                        arrivals = int(row[filter_by_list_index[3]])
                        
                        if arrivals == "":
                            arrivals = 0
                        
                        arrivals = self.check_for_jump(unit, arrivals, task_time)
                        
                        post_time = self.convert_to_minutes(row[filter_by_list_index[4]])
                        
                        crew = row[filter_by_list_index[5]]

                        post_assignments = int(row[filter_by_list_index[6]])

                        if len(crew) > 0:
                            crew = crew.split("&")
                            crew_member_one = crew[0]
                            crew_member_two = crew[1]
                            crew_member_one = crew_member_one.strip()
                            crew_member_two = crew_member_two.strip()
                        else:
                            crew_member_one = "N/A"
                            crew_member_two = "N/A"

                        voidUnits = ["H", "7", "5", "E"]

                        unitExists = self.liveWorkload.find_one({"unit" : unit})
                        if unitExists:
                            status = unitExists["status"]
                            above_max = unitExists["above_max"]
                            above_current = unitExists["above_current"]
                            late_call = unitExists["late_call"]
                            past_eos = unitExists["past_eos"]
                            drive_time = unitExists["drive_time"]
                            on_call_time = unitExists["on_call_time"]
                            last_task_time = unitExists["task_time"]
                            last_post_time = unitExists["post_time"]
                            last_post = unitExists["last_post"]
                            last_arrivals = unitExists["arrivals"]
                        else:
                            status = None
                            above_max = False
                            above_current = False
                            late_call = False
                            past_eos = False
                            drive_time = 0
                            on_call_time = 0
                            last_task_time = 0
                            last_post_time = 0
                            last_post = 0
                            last_arrivals = 0

                        if unit[0] not in voidUnits:
                            self.csvData.append({
                                "updated_at" : current_time,
                                "unit" : unit,
                                "sos" : sos,
                                "task_time" : task_time,
                                "arrivals" : arrivals,
                                "post_time" : post_time,
                                "crew_member_one" : crew_member_one,
                                "crew_member_two" : crew_member_two,
                                "workload" : 0,
                                "threshold" : 0,
                                "ratio" : 0,
                                "status" : status,
                                "above_max" : above_max,
                                "above_current" : above_current,
                                "late_call" : late_call,
                                "past_eos" : past_eos,
                                "drive_time" : drive_time,
                                "on_call_time" : on_call_time,
                                "last_task_time" : last_task_time,
                                "last_post_time" : last_post_time,
                                "last_post" : last_post,
                                "last_arrivals" : last_arrivals,
                                "post_assignments" : post_assignments
                            })