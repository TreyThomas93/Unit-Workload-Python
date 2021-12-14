from assets.datetimeTZ import datetime_tz
from datetime import datetime, timedelta

class Unit:
    """ Unit class creates a unit object representing each unit in the system.
        Each object will include attributes representing crew, workload number, current threshold, current status.
    """
    total_units = 0
    max_threshold = 1
    max_task = 70

    def __init__(self, crew, unit_number, start_of_shift):
        """ static attributes """
        self.crew = crew
        self.unit_number = unit_number
        self.start_of_shift = start_of_shift
        self.end_of_shift = datetime.strptime(start_of_shift, '%H:%M:%S') + timedelta(hours=12)
        """ dynamic attributes """
        self.unit_data = {}
        # class attributes
        Unit.total_units += 1

    def unitWorkload(self):
        # Get Time Difference Between Start Of Shift & Current Time 
        tdelta = str(datetime.strptime(datetime_tz().split(" ")[-1], '%H:%M:%S') - datetime.strptime(self.start_of_shift, '%H:%M:%S'))
        hours_diff = float(tdelta[:4].replace(":", "."))
        # Get Percentage Of Shift Currently Worked 
        percentage_worked = round(hours_diff / 12, 2)
        # Set Max Threshold and Determine Current Threshold 
        current_threshold = (Unit.max_threshold / 12) * round(hours_diff, 2)
        # Check If Arrivals Above Zero 
        if self.unit_data["arrivals"] > 0:
            # Set Max Task and Get Task Differential 
            # true_task = (self.unit_data["task_time"] / self.unit_data["arrivals"])
            task_dif = Unit.max_task + self.unit_data["task_time"]
            # Workload Formula 
            workload = round(((percentage_worked / task_dif) * 100) + (self.unit_data["arrivals"] / 10), 2)
            workload = workload - (self.unit_data["post_time"] / 100) 
        # If Arrivals Not More Than Zero, Workload = Current Threshold 
        else:
            workload = ( current_threshold - (self.unit_data["post_time"] / 100))
            
        self.unit_data["current_workload"] = round(workload, 2)
        self.unit_data["current_threshold"] = round(current_threshold, 2)

    def unitStatus(self):
        pass

    def __repr__(self):
        """ Displays a representation of the current object. 
            Display will show unit number, crew, unit workload, unit status
        """
        return f"Unit: {self.unit_number} - Crew: {', '.join(self.crew)} - Workload: {self.unit_data.get('current_workload')} - Status: {self.unit_data.get('current_status')}"