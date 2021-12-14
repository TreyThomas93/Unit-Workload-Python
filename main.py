from random import randint
from pprint import pprint
from units import Unit
from assets.datetimeTZ import datetime_tz
from datetime import datetime
from unit_data import units
import pandas as pd
from tabulate import tabulate
import matplotlib.pyplot as plt

class Main:

    def __init__(self):
        self.units = []

    def createUnitObjects(self, _units):
        for unit_number, value in _units.items():
            unit = Unit(value["crew"], unit_number, value["sos"])
            self.units.append(unit)

    def generateDataForUnits(self):
        for unit in self.units:
            minutes_from_start =(datetime.strptime(datetime_tz().split(" ")[-1], '%H:%M:%S') - datetime.strptime(unit.start_of_shift, '%H:%M:%S')).total_seconds() // 60
            while True:
                arrivals = randint(0, 12)
                task_time = randint(40, 90)
                if task_time * arrivals <= minutes_from_start:
                    break
            task_time = task_time if arrivals > 0 else 0
            while True:
                post_time = randint(0, minutes_from_start)
                result = minutes_from_start - (task_time * arrivals)
                if post_time <= result:
                    break

            obj ={
                "task_time": task_time,
                "arrivals": arrivals,
                "post_time": post_time,
                "last_updated": datetime_tz()
            }
            unit.unit_data.update(obj)

if __name__ == '__main__':
    main = Main()
    main.createUnitObjects(units)
    main.generateDataForUnits()

    for unit in main.units:
        unit.unitWorkload()

    units = sorted(main.units, key = lambda i: i.unit_data['current_threshold'])

    # units = [{"Unit" : unit.unit_number, "Crew" : ", ".join(unit.crew), "Current_Workload" : unit.unit_data["current_workload"], "Task_Time" : unit.unit_data["task_time"], "Post_Time" : unit.unit_data["post_time"], "Arrivals" : unit.unit_data["arrivals"]} for unit in units]
    # df = pd.DataFrame(units)
    # df = df.set_index("Unit")
    # print(tabulate(df, showindex=True, headers=df.columns))