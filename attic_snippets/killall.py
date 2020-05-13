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
    if x.startswith("arangodb"):
        print('killing ' + str(process))
        process.kill()
    elif x.startswith("arangod"):
        arangods += [process]
time.sleep(5)
for arangod in arangods:
    print('killing ' + str(arangod))
    arangod.kill()
print('done')
time.sleep(5)
