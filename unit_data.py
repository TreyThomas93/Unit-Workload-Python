import names
from assets.datetimeTZ import datetime_tz
from datetime import date, datetime, timedelta
from random import randint
from pprint import pprint

def getCrewMembers():
    _names = [names.get_full_name() for _ in range(62)]
    i = 2
    crew_members = []
    for _ in range(int(len(_names)/2)):
        crew = tuple(_names[i-2:i])
        crew_members.append(crew)
        i+=2
    return crew_members

def getUnits(crew_members):
    units = []
    while len(units) <= (len(crew_members)):
        unit = randint(101, 149)
        if unit not in units:
            units.append(unit)
    return units

def getStartTimes(crew_members):
    start_times = []
    while len(start_times) <= (len(crew_members)):
        _hour = randint(4, 20)
        if _hour < 10:
            hour = f"0{_hour}:00:00"
        else:
            hour = f"{_hour}:00:00"
        # Get Time Difference Between Start Of Shift & Current Time 
        tdelta = str(datetime.strptime(datetime_tz().split(" ")[-1], '%H:%M:%S') - datetime.strptime(hour, '%H:%M:%S'))
        hours_diff = float(tdelta[:4].replace(":", "."))
        # Get Percentage Of Shift Currently Worked 
        percentage_worked = round(hours_diff / 12, 2)
        dt = datetime.strptime(datetime_tz(), "%m/%d/%y %H:%M:%S")
        sos = dt.replace(hour=_hour, minute=0, second=0)
        if dt >= sos and percentage_worked <= 1:
            start_times.append(sos.strftime("%H:%M:%S"))
    return start_times

def getTaskTimesAndArrivals(start_times):
    task_times = []
    _arrivals = []
    for sos in start_times:
        minutes_from_start = (datetime.strptime(datetime_tz().split(" ")[-1], '%H:%M:%S') - datetime.strptime(sos, '%H:%M:%S')).total_seconds() // 60
        while True:
            arrivals = randint(0, 12)
            task_time = randint(40, 90)
            if task_time * arrivals <= minutes_from_start:
                break
        task_times.append(task_time if arrivals > 0 else 0)
        _arrivals.append(arrivals)
    return task_times, _arrivals

def getPostTimes(start_times, task_times, _arrivals):
    post_times = []
    for sos, task_time, arrivals in zip(start_times, task_times, _arrivals):
        minutes_from_start = (datetime.strptime(datetime_tz().split(" ")[-1], '%H:%M:%S') - datetime.strptime(sos, '%H:%M:%S')).total_seconds() // 60
        while True:
            post_time = randint(0, minutes_from_start)
            result = minutes_from_start - (task_time * arrivals)
            if post_time <= result:
                break
        post_times.append(post_time)
    return post_times
    
    

crew_members = getCrewMembers()
units = getUnits(crew_members)
start_times = getStartTimes(crew_members)
task_times, _arrivals = getTaskTimesAndArrivals(start_times)
post_times = getPostTimes(start_times, task_times, _arrivals)

units = [{"unit" : unit, "crew" : names, "sos" : sos, "task_time" : task_time, "arrivals" : arrivals, "post_time" : post_time} for unit, names, sos, task_time, arrivals, post_time in zip(units, crew_members, start_times, task_times, _arrivals, post_times)]