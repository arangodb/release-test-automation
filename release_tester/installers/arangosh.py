import os
import psutil
import installers.log as loglog
log = loglog.log


class arangoshExecutor(object):
    def __init__(self, config):
        self.cfg = config

    def runCommand(self, cmd):
        cmd = [os.path.join(self.cfg.basePath, "usr/bin/arangosh"),
               "--server.endpoint", "tcp://127.0.0.1:%d" %(int(self.cfg.port)),
               "--server.username", "%s" % (self.cfg.username),
               "--server.password", "%s" % (self.cfg.passvoid),
               "--javascript.execute-string", "%s" % (cmd[0])]

        log("launching " + cmd[1])
        # PIPE=subprocess.PIPE
        log(str(cmd))
        p = psutil.Popen(cmd)#, stdout=PIPE, stdin=PIPE, stderr=PIPE, universal_newlines=True)
        return p.wait(timeout=30) == 0
