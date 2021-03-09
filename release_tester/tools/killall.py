#!/usr/bin/env python3
""" tiny utility to kill all arangodb related processes """
import logging
import psutil

def get_all_processes(kill_selenium):
    """ fetch all possible running processes that we may have spawned """
    arangods = []
    arangodbs = []
    arangobenchs = []
    arangosyncs = []
    chromedrivers = []
    headleschromes = []
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
            elif name.startswith('chromedriver') and kill_selenium:
                chromedrivers.append(psutil.Process(process.pid))
            elif name.startswith('chrom') and kill_selenium:
                process = psutil.Process(process.pid)
                if any('--headless' in s for s in process.cmdline()):
                    headleschromes.append(process)

        except Exception as ex:
            logging.error(ex)
    return (
        arangodbs +
        arangosyncs +
        arangods +
        arangobenchs +
        chromedrivers +
        headleschromes)

def kill_all_processes(kill_selenium=True):
    """killall arangod arangodb arangosync """
    processlist = get_all_processes(kill_selenium)
    print(processlist)
    for process in processlist:
        if process.is_running():
            logging.info("cleanup killing ${proc}".format(proc=process))
            if process.is_running():
                try:
                    process.terminate()
                except Exception as ex:
                    logging.info("seems as if process %s is already dead?",
                                 str(process) + " - " + str(ex))
                    continue
            if process.is_running():
                try:
                    process.wait(timeout=2)
                except psutil.NoSuchProcess:
                    pass
                except psutil.TimeoutExpired:
                    logging.info("timeout while waiting for %s to exit, try once more",
                                 str(process))
                try:
                    process.kill()
                except psutil.NoSuchProcess:
                    pass
