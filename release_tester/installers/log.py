import datetime
import time

def timestamp():
    return datetime.datetime.utcnow().isoformat()
def log(string):
    print(timestamp() + " " + string)
