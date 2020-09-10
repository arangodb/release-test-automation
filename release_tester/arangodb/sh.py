#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """
import logging
import psutil
import os
import tools.loghelper as lh
import tools.errorhelper as eh
import time
from pathlib import Path

from subprocess import DEVNULL, PIPE, Popen
from threading  import Thread
from queue import Queue, Empty
import sys
from tools.asciiprint import ascii_print, print_progress as progress

ON_POSIX = 'posix' in sys.builtin_module_names

def enqueue_stdout(std_out, queue):
    for line in iter(std_out.readline, b''):
        #print("O: " + str(line))
        queue.put(line)
    #print('0 done!')
    queue.put(-1)
    std_out.close()
def enqueue_stderr(std_err, queue):
    for line in iter(std_err.readline, b''):
        #print("E: " + str(line))
        queue.put(line)
    #print('1 done!')
    queue.put(-1)
    std_err.close()

class ArangoshExecutor():
    """ configuration """
    def __init__(self, config):
        self.cfg = config
        self.read_only = False

    def run_command(self, cmd, verbose=True):
        """ launch a command, print its name """
        run_cmd = [
            self.cfg.bin_dir / "arangosh",
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
            arangosh_run = psutil.Popen(run_cmd, stdout = DEVNULL, stderr = DEVNULL)

        exitcode = arangosh_run.wait(timeout=60)
        # logging.debug("exitcode {0}".format(exitcode))
        return exitcode == 0

    def self_test(self):
        """ run a command that throws to check exit code handling """
        logging.info("running arangosh check")
        success = self.run_command((
            'check throw exit codes',
            "throw 'yipiahea motherfucker'"),
                                   self.cfg.verbose)
        logging.debug("sanity result: " + str(success) + " - expected: False")

        if success:
            raise Exception("arangosh doesn't exit with non-0 to indicate errors")

        success = self.run_command((
            'check normal exit',
            'let foo = "bar"'),
                                   self.cfg.verbose)

        logging.debug("sanity result: " + str(success) + " - expected: True")

        if not success:
            raise Exception("arangosh doesn't exit with 0 to indicate no errors")

    def run_script(self, cmd, verbose = True):
        """ launch an external js-script, print its name """
        run_cmd = [
            self.cfg.bin_dir / "arangosh",
            "--server.endpoint",
            "tcp://127.0.0.1:{cfg.port}".format(cfg=self.cfg)
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
            arangosh_run = psutil.Popen(run_cmd, stdout = DEVNULL, stderr = DEVNULL)

        exitcode = arangosh_run.wait(timeout=30)
        logging.debug("exitcode {0}".format(exitcode))
        return exitcode == 0

    def run_script_monitored(self, cmd, args, timeout, verbose=True):
        run_cmd = [
            self.cfg.bin_dir / "arangosh",
            "--server.endpoint",
            "tcp://127.0.0.1:{cfg.port}".format(cfg=self.cfg),
            "--log.foreground-tty", "true"
        ]

        run_cmd += [ "--server.username", str(self.cfg.username) ]
        run_cmd += [ "--server.password", str(self.cfg.passvoid) ]

        run_cmd += [ "--javascript.execute", str(cmd[1]) ]

        if len(cmd) > 2:
            run_cmd += cmd[2:]

        if len(args) > 0:
            run_cmd += ['--'] + args

        arangosh_run = None
        if verbose:
            lh.log_cmd(run_cmd)
        p = Popen(run_cmd, stdout=PIPE, stderr=PIPE, close_fds=ON_POSIX)
        q = Queue()
        t1 = Thread(target=enqueue_stdout, args=(p.stdout, q))
        t2 = Thread(target=enqueue_stderr, args=(p.stderr, q))
        t1.start()
        t2.start()

        # ... do other things here
        # out = logfile.open('wb')
        # read line without blocking
        have_timeout = False
        count = 0
        tcount = 0
        close_count = 0
        result = []
        while not have_timeout:
            if not verbose:
                progress("sj" + str(tcount))
            line = ''
            try:
                line = q.get(timeout=1)
            except Empty:
                tcount += 1
                if verbose:
                    progress('T ' + str(tcount))
                have_timeout = tcount >= timeout
            else:
                tcount = 0
                if isinstance(line, bytes):
                    if verbose:
                       print("e: " + str(line))
                    if not str(line).startswith('#'):
                        result.append(line)
                else:
                    close_count += 1
                    if close_count == 2:
                        print(' done!')
                        break
        if have_timeout:
            print(" TIMEOUT OCCURED!")
            p.kill()
        rc = p.wait()
        t1.join()
        t2.join()
        if have_timeout or rc != 0:
            return False
        if len(result) == 0:
            return True
        return result

    def run_testing(self, testcase, args, timeout, logfile, verbose):
        args = [
            self.cfg.bin_dir / "arangosh",
            '-c', str(self.cfg.cfgdir / 'arangosh.conf'),
            '--log.level', 'warning',
            '--server.endpoint', 'none',
            '--javascript.allow-external-process-control', 'true',
            '--javascript.execute', str(Path('UnitTests') / 'unittest.js'),
            '--',
            testcase, '--testBuckets'] + args
        print(args)
        os.chdir(self.cfg.package_dir)
        p = Popen(args, stdout=PIPE, stderr=PIPE, close_fds=ON_POSIX)
        q = Queue()
        t1 = Thread(target=enqueue_stdout, args=(p.stdout, q))
        t2 = Thread(target=enqueue_stderr, args=(p.stderr, q))
        t1.start()
        t2.start()

        # ... do other things here
        out = logfile.open('wb')
        # read line without blocking
        count = 0
        while True:
            print(".", end="")
            line = ''
            try:
                line = q.get(timeout=1)
            except Empty:
                progress('-')
            else:
                #print(line)
                if line == -1:
                    count += 1
                    if count == 2:
                        print('done!')
                        break
                else:
                    out.write(line)
                    #print(line)
        t1.join()
        t2.join()

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
        res = self.run_command(['check version', js_script_string], self.cfg.verbose)
        logging.debug("version check result: " + str(res))

        if not res:
            eh.ask_continue_or_exit("version check failed", self.cfg.interactive)
        return res

    def hotbackup_create_nonbackup_data(self):
        """ create a collection with documents after taking a backup to verify its not in the backup """
        logging.info("creating volatile testdata")
        js_script_string = """
            db._create("this_collection_will_not_be_backed_up");
            db.this_collection_will_not_be_backed_up.save({"this": "document will be gone"});
        """
        logging.debug("script to be executed: " + str(js_script_string))
        res = self.run_command(['create volatile data', js_script_string], True) # self.cfg.verbose)
        logging.debug("data create result: " + str(res))

        if not res:
            eh.ask_continue_or_exit("creating volatile testdata failed", self.cfg.interactive)
        return res

    def hotbackup_check_for_nonbackup_data(self):
        """ check whether the data is in there or not. """
        logging.info("running version check")
        #  || db.this_collection_will_not_be_backed_up._length() != 0 // do we care?
        js_script_string = """
            if (db._collection("this_collection_will_not_be_backed_up") != null) {
              throw `data is there!`;
            }
        """
        logging.debug("script to be executed: " + str(js_script_string))
        res = self.run_command(['check whether non backup data exists', js_script_string], True) # self.cfg.verbose)
        logging.debug("data check result: " + str(res))
        
        return res

    def create_test_data(self, testname, args=[]):
        """ deploy testdata into the instance """
        if testname:
            logging.info("adding test data for {0}".format(testname))
        else:
            logging.info("adding test data")

        ret = self.run_script_monitored(cmd=[
            'setting up test data',
            self.cfg.test_data_dir / 'makedata.js'],
                                            args =args +[
                                                '--progress', 'true'
                                            ],
                                            timeout=100,
                                            verbose=self.cfg.verbose)

        return ret

    def check_test_data(self, testname, args=[]):
        """ check back the testdata in the instance """
        if testname:
            logging.info("checking test data for {0}".format(testname))
        else:
            logging.info("checking test data")

        ret = self.run_script_monitored(cmd=[
            'checking test data integrity',
            self.cfg.test_data_dir / 'checkdata.js'],
                                            args=args + [
                                                '--progress', 'true'
                                            ],
                                            timeout=5,
                                            verbose=self.cfg.verbose)

        return ret

    def clear_test_data(self, testname, args=[]):
        """ flush the testdata from the instance again """
        if testname:
            logging.info("removing test data for {0}".format(testname))
        else:
            logging.info("removing test data")

        ret = self.run_script_monitored(cmd=[
            'cleaning up test data',
            self.cfg.test_data_dir / 'cleardata.js'],
                                            args=args + [
                                                '--progress', 'true'
                                            ],
                                            timeout=5,
                                            verbose=self.cfg.verbose)

        return ret
