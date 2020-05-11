#!/usr/bin/env python3
""" tiny utility to kill all arangodb related processes """
import logging
import psutil
import signal
import os

def get_all_processes():
    arangods = []
    arangodbs = []
    arangosyncs = []
    logging.info("searching for leftover processes")
    for process in psutil.process_iter(['pid', 'name']):
        try:
            name = process.name()
            if name.startswith('arangodb'):
                arangodbs.append(psutil.Process(process.pid))
            elif name.startswith('arangod'):
                arangods.append(psutil.Process(process.pid))
            elif name.startswith('arangosync'):
                arangosyncs.append(psutil.Process(process.pid))
        except Exception as x:
            logging.error(x)
    return arangodbs + arangosyncs + arangods

def kill_all_processes():
    """killall arangod arangodb arangosync """
    processlist = get_all_processes()
    print(processlist)
    for process in processlist:
        if process.is_running():
            logging.info("cleanup killing ${proc}".format(proc=process))
            process.terminate()
            process.wait()
