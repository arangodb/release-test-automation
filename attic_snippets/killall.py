import psutil
import time

arangods = []
for process in psutil.process_iter(['pid', 'name']):
    x=""
    try:
        x = process.name()
    except: # access denied...
        x = ""
        continue
    if x == "arangodb.exe":
        print('killing ' + str(process))
        process.kill()
    elif x == "arangod.exe":
        arangods += [process]
time.sleep(5)
for arangod in arangods:
    print('killing ' + str(arangod))
    arangod.kill()
print('done')
time.sleep(5)
