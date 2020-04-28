#!/usr/bin/env python3
""" tiny utility to kill all arangodb related processes """
import logging
import psutil
import signal
import os
import time
import sys
def handler(signum, frame):
    print("signal!")
    if signum == signal.SIGINT:
        print('Signal SIGINT received')
        exit(1)
    if signum == signal.SIGBREAK:
        print('Signal  CTRL_BREAK_EVENT received')
        exit(1)
    if signum == signal.CTRL_C_EVENT:
        print('Signal  signal.CTRL_C_EVENT received')
        exit(1)

print("x" * 80 + sys.argv[1])
print("%s - %d" % (sys.argv[1], os.getpid()))
signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGBREAK, handler)
while True:
    print(sys.argv[1])
    time.sleep(0.5)
