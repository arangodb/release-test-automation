#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """
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
                   "--server.endpoint",
                   "tcp://127.0.0.1:%d" % (int(self.cfg.port)),
                   "--server.username", "%s" % (self.cfg.username),
                   "--server.password", "%s" % (self.cfg.passvoid),
                   "--javascript.execute-string", "%s" % (cmd[1])]

        if len(cmd) > 2:
            run_cmd += cmd[2:]

        logging.info("launching %s", cmd[0])
        # PIPE=subprocess.PIPE
        print(str(run_cmd))
        arangosh_run = psutil.Popen(run_cmd)
        exitcode = arangosh_run.wait(timeout=30)
        return exitcode == 0

    def run_script(self, cmd):
        """ launch an external js-script, print its name """
        run_cmd = [os.path.join(self.cfg.installPrefix, "usr/bin/arangosh"),
                   "--server.endpoint",
                   "tcp://127.0.0.1:%d" % (int(self.cfg.port)),
                   "--server.username", "%s" % (self.cfg.username),
                   "--server.password", "%s" % (self.cfg.passvoid),
                   "--javascript.execute", "%s" % str(cmd[1])]

        if len(cmd) > 2:
            run_cmd += cmd[2:]

        logging.info("launching %s", cmd[0])
        # PIPE=subprocess.PIPE
        print(str(run_cmd))
        arangosh_run = psutil.Popen(run_cmd)
        exitcode = arangosh_run.wait(timeout=30)
        return exitcode == 0

    def js_version_check(self):
        """ run a version check command; this can double as password check """
        return self.run_command((
            'check version',
            "if (db._version()!='%s') { throw 'fail'}" % (self.cfg.version)))

    def create_test_data(self):
        """ deploy testdata into the instance """
        return self.run_script([
            'setting up test data',
            self.cfg.test_data_dir / 'makedata.js'])

    def check_test_data(self):
        """ check back the testdata in the instance """
        self.run_script([
            'checking test data integrity',
            self.cfg.test_data_dir / 'checkdata.js'])

    def clear_test_data(self):
        """ flush the testdata from the instance again """
        self.run_script([
            'cleaning up test data',
            self.cfg.test_data_dir / 'cleardata.js'])
