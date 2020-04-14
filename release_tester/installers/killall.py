#!/usr/bin/env python3

import logging
import psutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


def kill_all_processes():
    """killall arangod arangodb arangosync """
    arangods = []
    arangodbs = []
    arangosyncs = []
    logging.info("searching for leftover processes")
    for process in psutil.process_iter(['pid', 'name']):
        if process.name() == 'arangod':
            arangods.append(psutil.Process(process.pid))
        if process.name() == 'arangodb':
            arangodbs.append(psutil.Process(process.pid))
        if process.name() == 'arangosync':
            arangosyncs.append(psutil.Process(process.pid))

    for process in arangosyncs:
        if process.is_running():
            logging.info("cleanup killing " + str(process))
            process.terminate()
            process.wait()
    for process in arangodbs:
        if process.is_running():
            logging.info("cleanup killing " + str(process))
            process.terminate()
            process.wait()
    for process in arangods:
        if process.is_running():
            logging.info("cleanup killing " + str(process))
            process.terminate()
            process.wait()
