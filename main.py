from random import randint
from pprint import pprint
from units import Unit
from assets.datetimeTZ import datetime_tz
from datetime import datetime
from unit_data import units
import pandas as pd
from tabulate import tabulate

class Main:

    def __init__(self):
        self.units = []

    def createUnitObjects(self, units):
        for unit in units:
            unit = Unit(unit)
            self.units.append(unit)

if __name__ == '__main__':
    main = Main()
    main.createUnitObjects(units)

    for unit in main.units:
        unit.unitWorkload()

    units = sorted(main.units, key = lambda i: i.current_threshold)

    units = [{"Unit" : unit.unit_number, "Crew" : ", ".join(unit.crew), "Current_Workload" : unit.current_workload, "Task_Time" : unit.task_time, "Post_Time" : unit.post_time, "Arrivals" : unit.arrivals, "SOS" : unit.start_of_shift} for unit in units]
    df = pd.DataFrame(units)
    df = df.set_index("Unit")
    print(tabulate(df, showindex=True, headers=df.columns))