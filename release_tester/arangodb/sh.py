#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """
import logging
import os
from pathlib import Path

from queue import Queue, Empty
from subprocess import DEVNULL, PIPE, Popen
import sys
from threading  import Thread
import psutil
from tools.asciiprint import print_progress as progress
import tools.errorhelper as eh
import tools.loghelper as lh

ON_POSIX = 'posix' in sys.builtin_module_names

def dummy_line_result(line):
    """ do nothing with the line... """
    #pylint: disable=W0104
    line

def enqueue_stdout(std_out, queue, instance):
    """ add stdout to the specified queue """
    for line in iter(std_out.readline, b''):
        #print("O: " + str(line))
        queue.put((line, instance))
    #print('0 done!')
    queue.put(-1)
    std_out.close()

def enqueue_stderr(std_err, queue, instance):
    """ add stderr to the specified queue """
    for line in iter(std_err.readline, b''):
        #print("E: " + str(line))
        queue.put((line, instance))
    #print('1 done!')
    queue.put(-1)
    std_err.close()

def convert_result(result_array):
    """ binary -> string """
    result = ""
    for one_line in result_array:
        result += "\n" + one_line[0].decode("unicode_escape").rstrip()
    return result

class ArangoshExecutor():
    """ configuration """
    def __init__(self, config, connect_instance):
        self.connect_instance = connect_instance
        self.cfg = config
        self.read_only = False

    def run_command(self, cmd, verbose=True):
        """ launch a command, print its name """
        run_cmd = [
            self.cfg.bin_dir / "arangosh",
            "--log.level", "v8=debug",
            "--server.endpoint", self.connect_instance.get_endpoint(),
            "--server.username", str(self.cfg.username),
            "--server.password", str(self.connect_instance.get_passvoid())]
        # if self.cfg.username:
        #    run_cmd += [ "--server.username", str(self.cfg.username) ]
        if self.cfg.passvoid:
            run_cmd += [ "--server.password", str(self.cfg.passvoid) ]

        run_cmd += ["--javascript.execute-string", str(cmd[1]) ]

        if len(cmd) > 2:
            run_cmd += cmd[2:]

        arangosh_run = None
        if verbose:
            lh.log_cmd(run_cmd)
            arangosh_run = psutil.Popen(run_cmd)
        else:
            arangosh_run = psutil.Popen(run_cmd,
                                        stdout = DEVNULL,
                                        stderr = DEVNULL)

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
            raise Exception(
                "arangosh doesn't exit with non-0 to indicate errors")

        success = self.run_command((
            'check normal exit',
            'let foo = "bar"'),
                                   self.cfg.verbose)

        logging.debug("sanity result: " + str(success) + " - expected: True")

        if not success:
            raise Exception(
                "arangosh doesn't exit with 0 to indicate no errors")

    def run_script(self, cmd, verbose = True):
        """ launch an external js-script, print its name """
        run_cmd = [
        # if self.cfg.username:
        #    run_cmd += [ "--server.username", str(self.cfg.username) ]

        # if self.cfg.passvoid:
        #    run_cmd += [ "--server.password", str(self.cfg.passvoid) ]

            self.cfg.bin_dir / "arangosh",
            "--log.level", "v8=debug",
            "--server.endpoint", self.connect_instance.get_endpoint(),
            "--server.username", str(self.cfg.username),
            "--server.password", str(self.connect_instance.get_passvoid()),
            "--javascript.execute", str(cmd[1]) ]

        if len(cmd) > 2:
            run_cmd += cmd[2:]

        arangosh_run = None
        if verbose:
            lh.log_cmd(run_cmd)
            arangosh_run = psutil.Popen(run_cmd)
        else:
            arangosh_run = psutil.Popen(run_cmd,
                                        stdout = DEVNULL,
                                        stderr = DEVNULL)

        exitcode = arangosh_run.wait(timeout=30)
        logging.debug("exitcode {0}".format(exitcode))
        return exitcode == 0

    def run_script_monitored(self, cmd, args, timeout, result_line,
                             process_control=False, verbose=True):
       # pylint: disable=R0913 disable=R0902 disable=R0915 disable=R0912 disable=R0914
        """
        runs a script in background tracing with
        a dynamic timeout that its got output
        (is still alive...)
        """
        if process_control:
            process_control = ['--javascript.allow-external-process-control', 'true']
        else:
            process_control = []
        run_cmd = [
            self.cfg.bin_dir / "arangosh",
            "--server.endpoint", self.connect_instance.get_endpoint(),
            "--log.level", "v8=debug",
            "--log.foreground-tty", "true",
            "--javascript.module-directory", self.cfg.test_data_dir.resolve(),
            "--server.username", str(self.cfg.username),
            "--server.password", str(self.connect_instance.get_passvoid())
        ] + process_control + [
            "--javascript.execute", str(cmd[1]) ]

        if len(args) > 0:
            run_cmd += ['--'] + args

        if verbose:
            lh.log_cmd(run_cmd)
        process = Popen(run_cmd,
                        stdout=PIPE, stderr=PIPE, close_fds=ON_POSIX,
                        cwd=self.cfg.test_data_dir.resolve())
        queue = Queue()
        thread1 = Thread(target=enqueue_stdout, args=(process.stdout,
                                                      queue,
                                                      self.connect_instance))
        thread2 = Thread(target=enqueue_stderr, args=(process.stderr,
                                                      queue,
                                                      self.connect_instance))
        thread1.start()
        thread2.start()

        # ... do other things here
        # out = logfile.open('wb')
        # read line without blocking
        have_timeout = False
        tcount = 0
        close_count = 0
        result = []
        while not have_timeout:
            if not verbose:
                progress("sj" + str(tcount))
            line = ''
            try:
                line = queue.get(timeout=1)
                result_line(line)
            except Empty:
                tcount += 1
                if verbose:
                    progress('T ' + str(tcount))
                have_timeout = tcount >= timeout
            else:
                tcount = 0
                if isinstance(line, tuple):
                    if verbose:
                        print("e: " + str(line[0]))
                    if not str(line[0]).startswith('#'):
                        result.append(line)
                else:
                    close_count += 1
                    if close_count == 2:
                        print(' done!')
                        break
        if have_timeout:
            print(" TIMEOUT OCCURED!")
            process.kill()
        rc_exit = process.wait()
        print(rc_exit)
        thread1.join()
        thread2.join()
        if have_timeout or rc_exit != 0:
            return (False, convert_result(result))
        if len(result) == 0:
            return (True, "")
        return (True, convert_result(result))

    def run_testing(self, testcase, args,
                    #timeout,
                    logfile,
                    #verbose
                    ):
       # pylint: disable=R0913 disable=R0902
        """ testing.js wrapper """
        args = [
            self.cfg.bin_dir / "arangosh",
            '-c', str(self.cfg.cfgdir / 'arangosh.conf'),
            '--log.level', 'warning',
            "--log.level", "v8=debug",
            '--server.endpoint', 'none',
            '--javascript.allow-external-process-control', 'true',
            '--javascript.execute', str(Path('UnitTests') / 'unittest.js'),
            '--',
            testcase, '--testBuckets'] + args
        print(args)
        os.chdir(self.cfg.package_dir)
        process = Popen(args, stdout=PIPE, stderr=PIPE, close_fds=ON_POSIX)
        queue = Queue()
        thread1 = Thread(target=enqueue_stdout, args=(process.stdout,
                                                      queue,
                                                      self.connect_instance))
        thread2 = Thread(target=enqueue_stderr, args=(process.stderr,
                                                      queue,
                                                      self.connect_instance))
        thread1.start()
        thread2.start()

        # ... do other things here
        out = logfile.open('wb')
        # read line without blocking
        count = 0
        while True:
            print(".", end="")
            line = ''
            try:
                line = queue.get(timeout=1)
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
        thread1.join()
        thread2.join()

    def js_version_check(self):
        """ run a version check command; this can double as password check """
        logging.info("running version check")
        semdict = dict(self.cfg.semver.to_dict())
        version = '{major}.{minor}.{patch}'.format(**semdict)
        js_script_string = """
            const version = db._version().substring(0, {1});
            if (version != "{0}") {{
                throw `version check failed: ${{version}} (current) !- {0} (requested)`
            }}
        """.format(version, len(version))

        logging.debug("script to be executed: " + str(js_script_string))
        res = self.run_command(['check version',
                                js_script_string],
                               self.cfg.verbose)
        logging.debug("version check result: " + str(res))

        if not res:
            eh.ask_continue_or_exit("version check failed",
                                    self.cfg.interactive)
        return res

    def js_set_passvoid(self, user, passvoid):
        """ connect to the instance, and set a passvoid for the user """
        js_set_passvoid_str = 'require("org/arangodb/users").update("%s", "%s");'% (
            user, passvoid)
        logging.debug("script to be executed: " + str(js_set_passvoid_str))
        res = self.run_command(['set passvoid',
                                js_set_passvoid_str],
                               self.cfg.verbose)
        logging.debug("set passvoid check result: " + str(res))

        if not res:
            eh.ask_continue_or_exit("setting passvoid failed",
                                    self.cfg.interactive)
        return res

    def hotbackup_create_nonbackup_data(self):
        """
        create a collection with documents after taking a backup
        to verify its not in the backup
        """
        logging.info("creating volatile testdata")
        js_script_string = """
            db._create("this_collection_will_not_be_backed_up");
            db.this_collection_will_not_be_backed_up.save(
               {"this": "document will be gone"});
        """
        logging.debug("script to be executed: " + str(js_script_string))
        res = self.run_command(['create volatile data',
                                js_script_string],
                               True) # self.cfg.verbose)
        logging.debug("data create result: " + str(res))

        if not res:
            eh.ask_continue_or_exit("creating volatile testdata failed",
                                    self.cfg.interactive)
        return res

    def hotbackup_check_for_nonbackup_data(self):
        """ check whether the data is in there or not. """
        logging.info("running version check")
        #  || db.this_collection_will_not_be_backed_up._length() != 0
        # // do we care?
        js_script_string = """
            if (db._collection("this_collection_will_not_be_backed_up")
                 != null) {
              throw `data is there!`;
            }
        """
        logging.debug("script to be executed: " + str(js_script_string))
        res = self.run_command(['check whether non backup data exists',
                                js_script_string],
                               True) # self.cfg.verbose)
        logging.debug("data check result: " + str(res))

        return res

    def run_in_arangosh(self, testname,
                        args=[], moreargs=[],
                        result_line=dummy_line_result,
                        timeout=100):
       # pylint: disable=R0913 disable=R0902 disable=W0102
        """ mimic runInArangosh testing.js behaviour """
        if testname:
            logging.info("adding test data for {0}".format(testname))
        else:
            logging.info("adding test data")

        ret = None

        try:
            cwd = Path.cwd()
            (cwd / '3rdParty').mkdir()
            (cwd / 'arangosh').mkdir()
            (cwd / 'arangod').mkdir()
            (cwd / 'tests').mkdir()
        except FileExistsError:
            pass
        ret = self.run_script_monitored(cmd=[
            'setting up test data',
            self.cfg.test_data_dir.resolve() / 'run_in_arangosh.js'],
                                        args = [testname] + args + [
                                            '--args'
                                        ] + moreargs,
                                        timeout=timeout,
                                        result_line=result_line,
                                        process_control=True,
                                        verbose=self.cfg.verbose)
        return ret

    def create_test_data(self, testname, args=[],
                         result_line=dummy_line_result,
                         timeout=100):
        # pylint: disable=W0102
        """ deploy testdata into the instance """
        if testname:
            logging.info("adding test data for {0}".format(testname))
        else:
            logging.info("adding test data")

        ret = self.run_script_monitored(cmd=[
            'setting up test data',
            self.cfg.test_data_dir.resolve() / 'makedata.js'],
                                            args =args +[
                                                '--progress', 'true',
                                                '--passvoid', self.cfg.passvoid
                                            ],
                                            timeout=timeout,
                                        result_line=result_line,
                                        verbose=self.cfg.verbose)

        return ret

    def check_test_data(self, testname,
                        supports_foxx_tests,
                        args=[],
                        result_line=dummy_line_result):
        # pylint: disable=W0102
        """ check back the testdata in the instance """
        if testname:
            logging.info("checking test data for {0}".format(testname))
        else:
            logging.info("checking test data")

        ret = self.run_script_monitored(
            cmd=[
            'checking test data integrity',
            self.cfg.test_data_dir.resolve() / 'checkdata.js'],
            args=args + [
                '--progress', 'true',
                '--oldVersion', self.cfg.version,
                '--testFoxx', 'true' if supports_foxx_tests else 'false'
            ],
            timeout=25,
            result_line=result_line,
            verbose=self.cfg.verbose)
        return ret

    def clear_test_data(self, testname, args=[], result_line=dummy_line_result):
        # pylint: disable=W0102
        """ flush the testdata from the instance again """
        if testname:
            logging.info("removing test data for {0}".format(testname))
        else:
            logging.info("removing test data")

        ret = self.run_script_monitored(cmd=[
            'cleaning up test data',
            self.cfg.test_data_dir.resolve() / 'cleardata.js'],
                                            args=args + [
                                                '--progress', 'true'
                                            ],
                                        timeout=5,
                                        result_line=result_line,
                                        verbose=self.cfg.verbose)

        return ret
