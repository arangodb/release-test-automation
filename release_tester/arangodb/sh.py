#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """
import logging
import psutil
import tools.loghelper as lh
import tools.errorhelper as eh
import subprocess


class ArangoshExecutor():
    """ configuration """
    def __init__(self, config):
        self.cfg = config
        self.read_only = False

    def run_command(self, cmd, verbose=True):
        """ launch a command, print its name """
        run_cmd = [self.cfg.bin_dir / "arangosh",
                   "--server.endpoint",
                   "tcp://127.0.0.1:{cfg.port}".format(cfg=self.cfg)
                  ]

        run_cmd += [ "--server.username", str(self.cfg.username) ]
        run_cmd += [ "--server.password", str(self.cfg.passvoid) ]

        # if self.cfg.username:
        #    run_cmd += [ "--server.username", str(self.cfg.username) ]

        # if self.cfg.passvoid:
        #    run_cmd += [ "--server.password", str(self.cfg.passvoid) ]

        run_cmd += [ "--javascript.execute-string", str(cmd[1]) ]

        if len(cmd) > 2:
            run_cmd += cmd[2:]

        arangosh_run = None
        if verbose:
            lh.log_cmd(run_cmd)
            arangosh_run = psutil.Popen(run_cmd)
        else:
            arangosh_run = psutil.Popen(run_cmd, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

        exitcode = arangosh_run.wait(timeout=30)
        # logging.debug("exitcode {0}".format(exitcode))
        return exitcode == 0

    def self_test(self):
        """ run a command that throws to check exit code handling """
        logging.info("running arangosh check")
        success = self.run_command((
            'check throw exit codes',
            "throw 'yipiahea motherfucker'"), False)
        logging.debug("sanity result: " + str(success) + " - expected: False")

        if success:
            raise Exception("arangosh doesn't exit with non-0 to indicate errors")

        success = self.run_command((
            'check normal exit',
            'let foo = "bar"'), False)

        logging.debug("sanity result: " + str(success) + " - expected: True")

        if not success:
            raise Exception("arangosh doesn't exit with 0 to indicate no errors")

    def run_script(self, cmd, verbose = True):
        """ launch an external js-script, print its name """
        run_cmd = [self.cfg.bin_dir / "arangosh",
                   "--server.endpoint",
                   "tcp://127.0.0.1:{cfg.port}".format(cfg=self.cfg),
                  ]

        run_cmd += [ "--server.username", str(self.cfg.username) ]
        run_cmd += [ "--server.password", str(self.cfg.passvoid) ]

        # if self.cfg.username:
        #    run_cmd += [ "--server.username", str(self.cfg.username) ]

        # if self.cfg.passvoid:
        #    run_cmd += [ "--server.password", str(self.cfg.passvoid) ]

        run_cmd += [ "--javascript.execute", str(cmd[1]) ]

        if len(cmd) > 2:
            run_cmd += cmd[2:]

        arangosh_run = None
        if verbose:
            lh.log_cmd(run_cmd)
            arangosh_run = psutil.Popen(run_cmd)
        else:
            arangosh_run = psutil.Popen(run_cmd, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

        exitcode = arangosh_run.wait(timeout=30)
        logging.debug("exitcode {0}".format(exitcode))
        return exitcode == 0

    def js_version_check(self):
        """ run a version check command; this can double as password check """
        logging.info("running version check")
        js_script_string = """
            const version = db._version().substring(0,5);
            if (version != "{0}") {{
                throw `version check failed: ${{version}} (current) !- {0} (requested)`
            }}
        """.format(str(self.cfg.version)[:5])
        logging.debug("script to be executed: " + str(js_script_string))
        res = self.run_command(['check version', js_script_string])
        logging.debug("version check result: " + str(res))

        if not res:
            eh.ask_continue_or_exit("version check failed", self.cfg.interactive)
        return res

    def create_test_data(self, testname):
        """ deploy testdata into the instance """
        if testname:
            logging.info("adding test data for {0}".format(testname))
        else:
            logging.info("adding test data")

        success = self.run_script([
            'setting up test data',
            self.cfg.test_data_dir / 'makedata.js'])

        return success

    def check_test_data(self, testname):
        """ check back the testdata in the instance """
        if testname:
            logging.info("checking test data for {0}".format(testname))
        else:
            logging.info("checking test data")

        success = self.run_script([
            'checking test data integrity',
            self.cfg.test_data_dir / 'checkdata.js'])

        return success

    def clear_test_data(self, testname):
        """ flush the testdata from the instance again """
        if testname:
            logging.info("removing test data for {0}".format(testname))
        else:
            logging.info("removing test data")

        success = self.run_script([
            'cleaning up test data',
            self.cfg.test_data_dir / 'cleardata.js'])

        return success
