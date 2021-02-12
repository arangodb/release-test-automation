#!/usr/bin/env python3
""" tiny utility to kill all arangodb related processes """
import logging
import psutil

def get_all_processes():
    """ fetch all possible running processes that we may have spawned """
    arangods = []
    arangodbs = []
    arangobenchs = []
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
            elif name.startswith('arangobench'):
                arangobenchs.append(psutil.Process(process.pid))

        except Exception as ex:
            logging.error(ex)
    return arangodbs + arangosyncs + arangods + arangobenchs

def kill_all_processes():
    """killall arangod arangodb arangosync """
    processlist = get_all_processes()
    print(processlist)
    for process in processlist:
        if process.is_running():
            logging.info("cleanup killing ${proc}".format(proc=process))
            if process.is_running():
                try:
                    process.terminate()
                except Exception as x:
                    logging.info("seems as if process %s is already dead?",
                                 str(process) + " - " + str(x))
                    continue
            if process.is_running():
                try:
                    process.wait(timeout=2)
                except:
                    pass
                try:
                    process.kill()
                except:
                    pass
