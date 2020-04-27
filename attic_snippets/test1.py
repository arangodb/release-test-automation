#!/usr/bin/env python3
""" tiny utility to kill all arangodb related processes """
import logging
import psutil
import signal
import os
import time

def handler(signum, frame):
    #print("Xsignal!")
    #if signum == signal.SIGINT:
    #    print('xSignal SIGINT received')
    #if signum == signal.SIGBREAK:
    #    print('xSignal  CTRL_BREAK_EVENT received')
    #if signum == signal.CTRL_C_EVENT:
    #    print('xSignal  signal.CTRL_C_EVENT received')
    return

print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
print(os.getpid())
signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGBREAK, handler)



process = psutil.Popen(['python', 'test2.py', 'a'])
process2 = psutil.Popen(['python', 'test2.py', 'b'])

pid = process.pid

print("A: " + str(pid))
print("B: " + str(process2.pid))
# process.send_signal(signal.CTRL_BREAK_EVENT)
print(pid)
print( os.getpid())

time.sleep(10)
#$signal.signal(signal.SIGINT, handler)
#signal.signal(signal.SIGBREAK, handler)
# signal.signal(signal.CTRL_C_EVENT, handler)
#os.kill(pid, signal.SIGINT) # signal.CTRL_BREAK_EVENT)
#process.signal(pid, signal.SIGINT) # signal.CTRL_BREAK_EVENT)
# process.signal(pid, signal.CTRL_BREAK_EVENT)
#process.signal(pid, signal.CTRL_C_EVENT)
#os.kill(pid, signal.CTRL_C_EVENT)
# os.kill(pid, signal.SIGINT)
#os.kill(pid,signal.SIGBREAK)
os.kill(pid, signal.CTRL_C_EVENT)
print("snaotehu")

for proc in psutil.process_iter(['pid', 'name']):
    print("snatoehu %s" % str(proc))
    if proc.pid == pid:
        logging.info("found process after killing: %s", str(proc))
        proc.wait()

time.sleep(10)
