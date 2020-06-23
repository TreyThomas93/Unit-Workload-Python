import os
from random import randint
from assets.currentDatetime import current_dateTime
from assets.errorHandler import checkError


from datetime import datetime, timedelta
import names


class GenerateFakeData():

    def __init__(self, liveWorkload):
        self.Data = []
        self.liveWorkload = liveWorkload

    @checkError
    def getTimeOnShift(self, sos):
        # Get Time Difference Between SOS & Current Time
        current_time = current_dateTime("Time")
        s1 = sos
        s2 = str(current_time).split(" ")[-1]

        FMT = '%H:%M:%S'
        tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)
        tdelta = str(tdelta).split(" ")[-1]

        hours_diff = tdelta[:4]
        return round(float(hours_diff.replace(":", ".")) * 60)

    @checkError
    def getTimes(self, arrivals, time_on_shift):
        task_time = time_on_shift * (randint(0, 100) / 100)

        if arrivals > 0:
            avg_task = task_time / arrivals
        else:
            return None

        if avg_task < 40 or avg_task > 80:
            return None

        # print(f"\nTASK TIME: {task_time}")
        # print(f"ARRIVALS: {arrivals}")
        # print(f"AVG TASK: {avg_task}")

        remaining = time_on_shift - task_time

        post_time = remaining * (randint(0, 100) / 100)

        drive_time = remaining - post_time

        # print(f"REMAINING: {remaining}")
        # print(f"POST TIME: {post_time}")
        # print(f"DRIVE TIME: {drive_time}\n")

        return (round(task_time), round(post_time), round(drive_time))

    @checkError
    def generateData(self):
        current_time = current_dateTime("Time")

        max_limit = int(current_time[0:2])

        min_limit = int(str(datetime.strptime(
            current_time, "%H:%M:%S") - timedelta(hours=13)).split(" ")[1][0:2])

        if min_limit >= max_limit and (max_limit > 20 and max_limit < 4):
            min_limit = 0
        elif max_limit >= 4 and max_limit < 13:
            min_limit = 4

        print(f"MAX: {max_limit}")
        print(f"MIN: {min_limit}")

        checkExisting = []
        while len(self.Data) < 20:
            unit = randint(10, 50)

            sos = f"{randint(min_limit, max_limit)}:00:00"
            time_on_shift = self.getTimeOnShift(sos)

            arrivals = randint(0, 10)

            response = self.getTimes(arrivals, time_on_shift)

            if response:

                task_time = response[0]
                post_time = response[1]
                drive_time = response[2]

                if drive_time > 0:
                    post_assignments = randint(1, 15)
                    if drive_time / post_assignments == 4:
                        continue
                else:
                    post_assignments = 0

                crew_member_one = names.get_full_name().split(" ")
                crew_member_two = names.get_full_name().split(" ")

                crew_member_one = f"{crew_member_one[1]}, {crew_member_one[0]}"
                crew_member_two = f"{crew_member_two[1]}, {crew_member_two[0]}"

                data = {
                    "updated_at": current_time,
                    "unit": unit,
                    "sos": sos,
                    "time_on_shift": time_on_shift,
                    "task_time": task_time,
                    "arrivals": arrivals,
                    "post_time": post_time,
                    "crew_member_one": crew_member_one,
                    "crew_member_two": crew_member_two,
                    "workload": 0,
                    "threshold": 0,
                    "ratio": 0,
                    "status": None,
                    "post_assignments": post_assignments,
                    "drive_time": drive_time
                }

                if unit not in checkExisting:
                    self.Data.append(data)
                    checkExisting.append(unit)
                    print(f"{unit} Added!")
