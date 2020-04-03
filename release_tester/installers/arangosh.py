#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh to the configured connection """
import os
import logging
import psutil


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class ArangoshExecutor():
    """ configuration """
    def __init__(self, config):
        self.cfg = config

    def run_command(self, cmd):
        """ launch a command, print its name """
        run_cmd = [os.path.join(self.cfg.installPrefix, "usr/bin/arangosh"),
                   "--server.endpoint", "tcp://127.0.0.1:%d" %(int(self.cfg.port)),
                   "--server.username", "%s" % (self.cfg.username),
                   "--server.password", "%s" % (self.cfg.passvoid),
                   "--javascript.execute-string", "%s" % (cmd[0])]

        logging.info("launching %s", cmd[1])
        # PIPE=subprocess.PIPE
        # print(str(runCmd))
        arangosh_run = psutil.Popen(run_cmd)
        exitcode = arangosh_run.wait(timeout=30)
        return exitcode == 0

    def js_version_check(self):
        """ run a version check command; this can double as password check """
        return self.run_command((
            "if (db._version()!='%s') { throw 'fail'}" % (self.cfg.version),
            'check version'))
