from assets.currentDatetime import current_dateTime
import os

def checkError(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error(func.__name__, e)

    return wrapper

def error(name, err):
    try:
        dt = current_dateTime("Date").replace("/", "_")
        error_log = f"{os.getcwd()}/master/logs/Error_Log_{dt}.txt"
        with open(error_log, "a") as f:
            f.write(
                f"ERROR OCCURED:// Name: {name} - Description: {err} - Datetime: {current_dateTime()}\n")
    except Exception as e:
        print(e)