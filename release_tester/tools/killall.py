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
            if name.endswith('.exe'):
                name = name[:-4]
            if name == 'arangod':
                arangods.append(psutil.Process(process.pid))
            elif name == 'arangodb':
                arangodbs.append(psutil.Process(process.pid))
            elif name == 'arangosync':
                arangosyncs.append(psutil.Process(process.pid))
            #else:
                # print(name)
        except Exception as x:
            print(x)
            pass
    return arangodbs + arangosyncs + arangods

def kill_all_processes():
    """killall arangod arangodb arangosync """
    processlist = get_all_processes()
    print(processlist)
    for process in processlist:
        if process.is_running():
            logging.info("cleanup killing %s", str(process))
            process.terminate()
            process.wait()
footgun = False
def handler(signum, frame):
    global footgun
    if not footgun:
        exit(1)
    pass
    #if signum == signal.SIGINT:
    #    print('Signal SIGINT received')
    #if signum == signal.SIGBREAK:
    #    print('Signal  CTRL_BREAK_EVENT received')
    #if signum == signal.CTRL_C_EVENT:
    #    print('Signal  signal.CTRL_C_EVENT received')
        
#def sig_int_process(process):
#    """ send process CTRL+C and check whether it terminated """
#    global footgun
#    pid = process.pid
#    # process.send_signal(signal.CTRL_BREAK_EVENT)
#    print(pid)
#    print( os.getpid())
#    signal.signal(signal.SIGINT, handler)
#    # signal.signal(signal.SIGBREAK, handler)
#    # signal.signal(signal.CTRL_C_EVENT, handler)
#    #os.kill(pid, signal.SIGINT) # signal.CTRL_BREAK_EVENT)
#    #process.signal(pid, signal.SIGINT) # signal.CTRL_BREAK_EVENT)
#    # process.signal(pid, signal.CTRL_BREAK_EVENT)
#    #process.signal(pid, signal.CTRL_C_EVENT)
#    #os.kill(pid, signal.CTRL_C_EVENT)
#    #os.kill(pid, signal.SIGINT)
#    #os.kill(pid,signal.SIGBREAK)
#    footgun = True
#    os.kill(pid, signal.CTRL_C_EVENT)
#    print("snaotehu")
#    process.wait()
#    footgun = False
#    #time.sleep(10)
#    print("slept")
#    print("santoehu")
#    for proc in psutil.process_iter(['pid', 'name']):
#        # print("snatoehu %s" % str(proc))
#        if proc.pid == pid:
#            logging.info("found process after killing: %s", str(proc))
#            proc.wait()
