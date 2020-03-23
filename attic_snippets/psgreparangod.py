import psutil
import time

for process in psutil.process_iter(['pid', 'name']):
    x=""
    try:
        x = process.name()
    except:
        x = ""
        continue
    if x == "arangod.exe":
        print(process.cmdline())
    if x == "arangodb.exe":
        print(process.cmdline())
