import pytz
from datetime import datetime

def current_dateTime(type=None):
    dt = datetime.now(tz=pytz.UTC).replace(microsecond=0)
    dt_central = dt.astimezone(pytz.timezone('US/Central'))
    dt = datetime.strftime(dt_central, "%m/%d/%y %H:%M:%S")
    if type == "Time":
        dt = dt.split()[1]
    elif type == "Date":
        dt = dt.split()[0]
    return dt