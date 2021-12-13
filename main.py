import names
from random import randint
from pprint import pprint
from units import Unit


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
    start_times.append(sos)

unit_obj = {unit:{"crew" : names, "sos" : sos} for unit, names, sos in zip(units, crew_members, start_times)}

class Main:

    def createUnitObjects(self):
        for unit_number, value in unit_obj.items():
            unit = Unit(value["crew"], unit_number, value["sos"])
            print(unit)

if __name__ == '__main__':
    main = Main()
    main.createUnitObjects()