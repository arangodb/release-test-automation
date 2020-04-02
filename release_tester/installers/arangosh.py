import os
import psutil
from logging import info as log
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

jsVersionCheck = (
    "if (db._version()!='%s') { throw 'fail'}" % (version),
    'check version')

class arangoshExecutor(object):
    def __init__(self, config):
        self.cfg = config

    def runCommand(self, cmd):
        runCmd = [os.path.join(self.cfg.installPrefix, "usr/bin/arangosh"),
               "--server.endpoint", "tcp://127.0.0.1:%d" %(int(self.cfg.port)),
               "--server.username", "%s" % (self.cfg.username),
               "--server.password", "%s" % (self.cfg.passvoid),
               "--javascript.execute-string", "%s" % (cmd[0])]

        log("launching " + cmd[1])
        # PIPE=subprocess.PIPE
        # print(str(runCmd))
        p = psutil.Popen(runCmd)#, stdout=PIPE, stdin=PIPE, stderr=PIPE, universal_newlines=True)
        x = p.wait(timeout=30)
        return x == 0
