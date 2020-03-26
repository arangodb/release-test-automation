import os
import psutil
from installers.log import log


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
        log(str(runCmd))
        p = psutil.Popen(runCmd)#, stdout=PIPE, stdin=PIPE, stderr=PIPE, universal_newlines=True)
        return p.wait(timeout=30) == 0
