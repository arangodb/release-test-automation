#!/usr/bin/env python3
""" tiny utility to kill all arangodb related processes """
import logging
import psutil
import signal
import os
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def get_all_processes():
    arangods = []
    arangodbs = []
    arangosyncs = []
    logging.info("searching for leftover processes")
    for process in psutil.process_iter(['pid', 'name']):
        try:
            name = process.name()
            if name.startswith('arangod'):
                arangods.append(psutil.Process(process.pid))
            elif name.startswith('arangodb'):
                arangodbs.append(psutil.Process(process.pid))
            elif name.startswith('arangosync'):
                arangosyncs.append(psutil.Process(process.pid))
        except Exception as x:
            print(x)
            pass # <-- Ist das die Behandlung die wir wollen?
    return arangodbs + arangosyncs + arangods # <-- wie waere es mit einem Tuple?

def kill_all_processes():
    """killall arangod arangodb arangosync """
    processlist = get_all_processes()
    print(processlist)
    for process in processlist:
        if process.is_running():
            logging.info("cleanup killing %s", str(process))
            process.terminate()
            process.wait()
