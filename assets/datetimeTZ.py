import pytz
from datetime import datetime

def datetime_tz():
    dt = datetime.now(tz=pytz.UTC).replace(microsecond=0)
    dt_central = dt.astimezone(pytz.timezone('US/Central'))
    return datetime.strftime(dt_central, "%m/%d/%y %H:%M:%S")