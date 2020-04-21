#!/usr/bin/env python3
""" tiny utility to kill all arangodb related processes """
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
        try:
            name = process.name()
            if name.endswith('.exe'):
                name = name[:-4]
            if name == 'arangod':
                arangods.append(psutil.Process(process.pid))
            elif name == 'arangodb':
                arangodbs.append(psutil.Process(process.pid))
            elif name == 'arangosync':
                arangosyncs.append(psutil.Process(process.pid))
            #else:
            #    print(name)
        except Exception as x:
            print(x)
            pass

    for processlist in [arangosyncs, arangodbs, arangods]:
        for process in processlist:
            if process.is_running():
                logging.info("cleanup killing %s", str(process))
                process.terminate()
                process.wait()
