from datetime import datetime
from assets.datetimeTZ import datetime_tz
from pprint import pprint

def unitWorkload(unit):
    max_threshold = 1
    max_task = 70
    sos = unit["sos"]
    arrivals = unit["arrivals"]
    task_time = unit["task_time"]
    post_time = unit["post_time"]
                
    # Get Time Difference Between SOS & Current Time 
    s1 = sos
    s2 = datetime_tz().split(" ")[-1]
    # s2 = "19:00:00"

    FMT = '%H:%M:%S'
    tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)
    tdelta = str(tdelta).split(" ")[-1]

    hours_diff = tdelta[:4]
    hours_diff = hours_diff.replace(":", ".")
    
    # Get Percentage Of Shift Currently Worked 
    percentage_worked = round(float(hours_diff) / 12, 2)
    
    # Set Max Threshold and Determine Current Threshold 
    current_threshold = (max_threshold / 12) * round(float(hours_diff), 2)
    
    # Check If Arrivals Above Zero 
    if arrivals > 0:
        # Set Max Task and Get Task Differential 
        # true_task = (task_time / arrivals)
        task_dif = max_task + task_time

        # Workload Formula 
        workload = round(((percentage_worked / task_dif) * 100) + (arrivals / 10), 2)
        workload = workload - (post_time / 100)
        
    # If Arrivals Not More Than Zero, Workload = Current Threshold 
    else:
        workload = ( current_threshold - (post_time / 100))
        
    unit["workload"] = round(workload, 2)
    unit["threshold"] = round(current_threshold, 2)
    unit["ratio"] = (round(workload, 2) - round(current_threshold, 2))

    pprint(unit)


unit = {
    "sos": "05:00:00",
    "arrivals": 10,
    "task_time" : 70,
    "post_time" : 100
}
unitWorkload(unit)