#!/usr/bin/env python3
import psutil
import signal
import os
import time
import subprocess

print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
print(os.getpid())
def handler(signum, frame):
    pass
signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGBREAK, handler)

kwargs = {}
kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
kwargs['bufsize'] = 1024


process = psutil.Popen(['python', 'test2.py', 'a'], shell=True) # creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
process2 = psutil.Popen(['python', 'test2.py', 'b'], shell=True) #  creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

pid = process.pid
print(process)
print(process.children())
print("A: " + str(pid))
print("B: " + str(process2.pid))
print(pid)
print( os.getpid())

time.sleep(1)
pythons  = [{}, {}]
for proc in psutil.process_iter(['pid', 'ppid', 'name']):
    print("next")
    print("next -> " + str(proc.pid))
    print("0 xxx %s" % str(proc.ppid()))
    print(str(proc))
    #if proc.pid == pid:
    #print("found process after killing: %s", str(proc))
    #proc.wait()
    if proc.ppid() == pid:
        print("0 python %s" % str(proc))
        pythons[0] = proc
    elif proc.ppid() == process2.pid:
        print("1 python %s" % str(proc))
        pythons[1] = proc
print("y"*80)
time.sleep(2)

os.kill(pid, signal.CTRL_C_EVENT)
print("2 huhu ")# + str(pythons[0].pid ))

print("1 bobo")
time.sleep(2)
os.kill(pid, signal.SIGBREAK)
print("3 bobo")
time.sleep(2)
os.kill(pid, signal.SIGINT)

print("1 bobo")
os.kill(process.pid, signal.SIGTERM)
os.kill(process2.pid, signal.SIGTERM)

os.kill(pythons[0].pid, signal.CTRL_C_EVENT)
print("2 huhu " + str(pythons[0].pid ))

time.sleep(2)
os.kill(pythons[0].pid, signal.SIGINT)
print("1 bobo")
ime.sleep(2)
os.kill(pythons[0].pid, signal.SIGBREAK)


print("1 bobo")
os.kill(process.pid, signal.SIGTERM)
os.kill(process2.pid, signal.SIGTERM)
