#!/usr/bin/env python3
""" tiny utility to kill all arangodb related processes """
import logging
import time
import json

# import platform
import collections

from reporting.reporting_utils import step
import psutil
from allure_commons._allure import attach

# yes, we catch all.
# pylint: disable=broad-except
NON_INT_PROC = [
    "kworker",
    "(udev-worker",
    "irq/",
    "scsi_",
    "migration",
    "ksoftirqd",
    "cpuhp",
    "rcu_",
    "ccp-",
    "ext4",
    "usb-storage",
]


def get_process_tree_recursive(parent, tree, indent=""):
    """get an ascii representation of the process tree"""
    text = ""
    try:
        name = psutil.Process(parent).name()
    except psutil.Error:
        name = "?"
    skip = False
    for blacklistitem in NON_INT_PROC:
        if name.startswith(blacklistitem):
            skip = True
    if skip:
        return ""
    text += f"{parent} {name}\n"
    if parent not in tree:
        return text
    children = tree[parent][:-1]
    for child in children:
        text += indent + "|- "
        text += get_process_tree_recursive(child, tree, indent + "| ")
    child = tree[parent][-1]
    text += indent + "`_ "
    text += get_process_tree_recursive(child, tree, indent + "  ")
    return text


def get_process_tree():
    """print a process tree"""
    print("xxxx")
    tree = collections.defaultdict(list)
    for process in psutil.process_iter():
        try:
            tree[process.ppid()].append(process.pid)
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            pass
    # on systems supporting PID 0, PID 0's parent is usually 0
    if 0 in tree and 0 in tree[0]:
        tree[0].remove(0)
    return get_process_tree_recursive(min(tree), tree)


@step
def get_all_processes(kill_selenium):
    """fetch all possible running processes that we may have spawned"""
    arangods = []
    arangodbs = []
    arangobenchs = []
    arangosyncs = []
    chromedrivers = []
    headleschromes = []
    others = []
    logging.info("searching for leftover processes")
    processes = psutil.process_iter()
    for process in processes:
        try:
            name = process.name()
            if name.startswith("arangodb"):
                arangodbs.append(psutil.Process(process.pid))
            elif name.startswith("arangod"):
                arangods.append(psutil.Process(process.pid))
            elif name.startswith("arangosh"):
                arangods.append(psutil.Process(process.pid))
            elif name.startswith("arangosync"):
                arangosyncs.append(psutil.Process(process.pid))
            elif name.startswith("arangobench"):
                arangobenchs.append(psutil.Process(process.pid))
            elif name.startswith("chromedriver") and kill_selenium:
                chromedrivers.append(psutil.Process(process.pid))
            elif name.startswith("chrom") and kill_selenium:
                process = psutil.Process(process.pid)
                if any("--headless" in s for s in process.cmdline()):
                    headleschromes.append(process)
            elif name.startswith("tshark"):
                others.append(psutil.Process(process.pid))

        except Exception as ex:
            logging.error(ex)
    return arangodbs + arangosyncs + arangods + arangobenchs + chromedrivers + headleschromes + others


@step
def kill_all_processes(kill_selenium=True):
    """killall arangod arangodb arangosync"""
    # pylint: disable=too-many-branches
    processlist = get_all_processes(kill_selenium)
    print(processlist)
    attach(str(processlist), "List of processes")
    for process in processlist:
        try:
            if process.status() == "zombie":
                process.wait(timeout=1)
                continue
        except psutil.TimeoutExpired:
            continue
        except psutil.NoSuchProcess:
            continue
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
                    logging.info(
                        "seems as if process %s is already dead?",
                        str(process) + " - " + str(ex),
                    )
                    continue
            if process.is_running():
                try:
                    process.wait(timeout=2)
                except psutil.NoSuchProcess:
                    pass
                except psutil.TimeoutExpired:
                    logging.info(
                        "timeout while waiting for %s to exit, try once more",
                        str(process),
                    )
                try:
                    process.kill()
                except psutil.NoSuchProcess:
                    pass


@step
def list_all_processes():
    """list all processes for later reference"""
    logging.info("PID  Process")
    # pylint: disable=catching-non-exception
    for process in psutil.process_iter(["pid", "name"]):
        try:
            cmdline = str(process.name())
            skip = False
            for blacklistitem in NON_INT_PROC:
                if cmdline.startswith(blacklistitem):
                    skip = True
            if skip:
                continue
            cmdline = str(process.cmdline())
            if cmdline == "[]":
                cmdline = "[" + process.name() + "]"
        except psutil.AccessDenied:
            pass
        except psutil.ZombieProcess:
            pass
        except ProcessLookupError:
            pass
        except psutil.NoSuchProcess:
            pass
        logging.info("{pid} {proc}".format(pid=process.pid, proc=cmdline))


def gather_process_thread_statistics(p):
    """ gather the statistics of one process and all its threads """
    ret = {}
    ret['process'] = [{
        'time': time.ctime(),
        'pid': p.pid,
        'ppid': p.ppid(),
        'cmdline': p.cmdline(),
        'name': p.name(),
        'percent': p.cpu_percent(),
        'iocounters': p.io_counters(),
        'ctxSwitches': p.num_ctx_switches(),
        'numfds': p.num_fds(),
        'cpu_times': p.cpu_times(),
        'meminfo': p.memory_full_info(),
        'netcons': p.connections()
    }]
    for t in p.threads():
        ret[ t.id ] = { 'user': t.user_time, 'sys': t.system_time}
    return ret

def add_delta(p1, p2):
    """ calculate and add a delta in cpu and time to all threads of a process """
    tids = list(p1.keys())
    for tid in tids:
        if tid in p2 and tid != 'process':
            p1[tid]['d_user'] = p2[tid]['user'] - p1[tid]['user']
            p1[tid]['d_sys'] = p2[tid]['sys'] - p1[tid]['sys']
    p1['process'].append(p2['process'][0])

def get_all_processes_stats_json():
    """ aggregate a structure of all processes and their threads plus delta """
    process_full_list = {}
    for n in [True, False]:
        processes = psutil.process_iter()
        for process in processes:
            name = ""
            try:
                name = process.name()
                if  process.ppid() != 2 and process.pid not in [1, 2]:
                    procstat = gather_process_thread_statistics(process)
                    if n:
                        process_full_list[f"p{process.pid}"] = procstat
                    else:
                        add_delta(process_full_list[f"p{process.pid}"], procstat)
            except psutil.AccessDenied:
                pass
            except Exception as ex:
                print(f"while inspecting {name}: {ex} ")
        if n:
            time.sleep(1)
    return json.dumps(process_full_list)
