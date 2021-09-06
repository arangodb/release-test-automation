#!/usr/bin/env python3
""" tiny utility to kill all arangodb related processes """
import logging

from reporting.reporting_utils import step
import psutil
from allure_commons._allure import attach
# yes, we catch all.
# pylint: disable=W0703

@step
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


@step
def kill_all_processes(kill_selenium=True):
    """killall arangod arangodb arangosync """
    processlist = get_all_processes(kill_selenium)
    print(processlist)
    attach(str(processlist), "List of processes")
    for process in processlist:
        if process.is_running():
            cmdline = str(process)
            try:
                cmdline = process.cmdline()
            except psutil.AccessDenied:
                pass
            except psutil.NoSuchProcess:
                pass
            logging.info("cleanup killing ${proc}".format(proc=cmdline))
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

@step
def list_all_processes():
    """ list all processes for later reference """
    pseaf = "PID  Process"
    for process in psutil.process_iter(['pid', 'name']):
        cmdline = process.name
        try:
            cmdline = str(process.cmdline())
            if cmdline == '[]':
                cmdline = '[' + process.name() + ']'
        except psutil.AccessDenied:
            pass
        logging.info("{pid} {proc}".format(pid = process.pid, proc=cmdline))
    print(pseaf)
