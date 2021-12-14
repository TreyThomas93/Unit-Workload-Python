import names
from random import randint
from pprint import pprint
from units import Unit
from assets.datetimeTZ import datetime_tz
from datetime import datetime, timedelta

class Main:

    def __init__(self):
        self.units = []

    def createUnitObjects(self, _units):
        for unit_number, value in _units.items():
            unit = Unit(value["crew"], unit_number, value["sos"])
            self.units.append(unit)

    def generateData(self):
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

    _names = [names.get_full_name() for _ in range(62)]
    i = 2
    crew_members = []
    for _ in range(int(len(_names)/2)):
        crew = tuple(_names[i-2:i])
        crew_members.append(crew)
        i+=2

    units = []
    while len(units) <= (len(crew_members)):
        unit = randint(101, 149)
        if unit not in units:
            units.append(unit)

    start_times = []
    while len(start_times) <= (len(crew_members)):
        sos = randint(4, 20)
        if sos < 10:
            sos = f"0{sos}:00:00"
        else:
            sos = f"{sos}:00:00"
        eos = (datetime.strptime(sos, "%H:%M:%S") + timedelta(hours=12)).strftime("%H:%M:%S")
        if sos <= datetime_tz().split(" ")[-1] <= eos:
            start_times.append(sos)

    units = {unit:{"crew" : names, "sos" : sos} for unit, names, sos in zip(units, crew_members, start_times)}
    main.createUnitObjects(units)
    main.generateData()

    for unit in main.units:
        unit.unitWorkload()
        if unit.unit_data["current_workload"] >= Unit.max_threshold:
            print(unit.start_of_shift)
            pprint(unit.unit_data)