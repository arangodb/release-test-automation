#!/usr/bin/env python3
""" class to manage an arangod or arangosync instance """
import datetime
import json
import logging
import re
import time
from abc import abstractmethod, ABC
from enum import IntEnum
from pathlib import Path

from allure_commons._allure import attach
from allure_commons.types import AttachmentType
from reporting.reporting_utils import step, attach_table
import psutil
import requests
from beautifultable import BeautifulTable
from requests.auth import HTTPBasicAuth
from tools.asciiprint import print_progress as progress


# log tokens we want to suppress from our dump:

LOG_BLACKLIST = [
    "2b6b3", # -> asio error, tcp connections died... so f* waht.
    "2c712", # -> agency connection died...
    "40e37"  # -> upgrade required TODO remove me from here, add system instance handling.
]

# log tokens we ignore in system ugprades...
LOG_SYSTEM_BLACKLIST = [
    "40e37"  # -> upgrade required
]
class InstanceType(IntEnum):
    """ type of arangod instance """
    COORDINATOR = 0
    RESILIENT_SINGLE = 1
    SINGLE = 2
    AGENT = 3
    DBSERVER = 4
    SYNCMASTER = 5
    SYNCWORKER = 6

INSTANCE_TYPE_STRING_MAP = {
    'coordinator': InstanceType.COORDINATOR,
    'resilientsingle': InstanceType.RESILIENT_SINGLE,
    'single': InstanceType.SINGLE,
    'agent': InstanceType.AGENT,
    'dbserver': InstanceType.DBSERVER,
    'syncmaster': InstanceType.SYNCMASTER,
    'syncworker': InstanceType.SYNCWORKER
}


def log_line_get_date(line):
    """ parse the date out of an arangod logfile line """
    return datetime.datetime.strptime(line.split(' ')[0], '%Y-%m-%dT%H:%M:%SZ')

class AfoServerState(IntEnum):
    """ in which sate is this active failover instance? """
    LEADER = 1
    NOT_LEADER = 2
    CHALLENGE_ONGOING = 3
    STARTUP_MAINTENANCE = 4
    NOT_CONNECTED = 5

class Instance(ABC):
    """abstract instance manager"""
    # pylint: disable=R0913 disable=R0902
    def __init__(self,
                 instance_type,
                 port,
                 basedir,
                 localhost,
                 publicip,
                 passvoid,
                 instance_string,
                 ssl
                 ):
        self.instance_type = INSTANCE_TYPE_STRING_MAP[instance_type]
        self.is_system = False
        self.type_str = list(INSTANCE_TYPE_STRING_MAP.keys())[int(self.instance_type.value)]
        self.port = port
        self.pid = None
        self.ppid = None
        self.basedir = basedir
        self.instance_string = instance_string
        self.logfile = basedir / (instance_string + '.log')
        self.instance_control_file = basedir / (instance_string + '_command.txt')
        self.localhost = localhost
        self.publicip = publicip
        self.passvoid = passvoid
        self.name = self.instance_type.name + str(self.port)
        self.instance = None
        self.serving = datetime.datetime(1970, 1, 1, 0, 0, 0)
        self.instance_arguments = []
        self.ssl = ssl

        logging.debug("creating {0.type_str} instance: {0.name}".format(self))

    @abstractmethod
    def detect_pid(self, ppid, offset, full_binary_path):
        """ gets the PID from the running process of this instance """

    def set_passvoid(self, passvoid):
        """ set the pw to connect to this instance """
        self.passvoid = passvoid

    def get_passvoid(self):
        """ retrieve the pw to connect to this instance """
        return self.passvoid

    def detect_gone(self, verbose=True):
        """ revalidate that the managed process is actualy dead """
        try:
            # we expect it to be dead anyways!
            return self.instance.wait(3) is None
        except psutil.TimeoutExpired:
            if not verbose:
                logging.error("was supposed to be dead, but I'm still alive? "
                              + repr(self))
            return False
        except AttributeError:
            #logging.error("was supposed to be dead, but I don't have an instance? "
            #              + repr(self))
            return True
        return True

    @abstractmethod
    def get_essentials(self):
        """ get the essential attributes of the class """

    def analyze_starter_file_line(self, line):
        """ instance specific analyzer function """
        #pylint: disable=W0107
        pass

    def load_starter_instance_control_file(self):
        """ load & parse the <instance_string>_command.txt file of the starter """
        if not self.instance_control_file.exists():
            raise FileNotFoundError("Instance control file not found! " +
                                    str(self.instance_control_file))
        self.instance_arguments = []
        with self.instance_control_file.open(errors='backslashreplace') as filedesc:
            for line in filedesc.readlines():
                line = line.rstrip().rstrip(' \\')
                self.analyze_starter_file_line(line)
                self.instance_arguments.append(line)

    def launch_manual_from_instance_control_file(self,
                                                 sbin_dir,
                                                 old_install_prefix,
                                                 new_install_prefix,
                                                 moreargs,
                                                 waitpid=True):
        """ launch instance without starter with additional arguments """
        self.load_starter_instance_control_file()
        command = [str(sbin_dir / self.instance_string)] + \
            self.instance_arguments[1:] + moreargs
        dos_old_install_prefix_fwd = str(old_install_prefix).replace("\\", "/")
        dos_new_install_prefix_fwd = str(new_install_prefix).replace("\\", "/")
        for i, cmd in enumerate(command):
            if cmd.find(str(old_install_prefix)) >= 0:
                command[i] = cmd.replace(
                    str(old_install_prefix), str(new_install_prefix))
            # the wintendo may have both slash directions:
            if cmd.find(dos_old_install_prefix_fwd) >= 0:
                command[i] = cmd.replace(
                    dos_old_install_prefix_fwd, dos_new_install_prefix_fwd)
        print("Manually launching: " + str(command))
        self.instance = psutil.Popen(command)
        print("instance launched with PID:" + str(self.instance.pid))
        if waitpid:
            exit_code = self.instance.wait()
            try:
                self.search_for_warnings()
            except Exception as ex:
                raise Exception(str(command) +
                                " exited with code: " +
                                str(exit_code)) from ex
            if exit_code != 0:
                raise Exception(str(command) +
                                " exited non zero: " +
                                str(exit_code))

    @step
    def rename_logfile(self, suffix='.old'):
        """ to ease further analysis, move old logfile out of our way"""
        logfile = str(self.logfile)
        new_logfile = Path(logfile + suffix)
        logging.info("renaming instance logfile: %s -> %s",
                     logfile, str(new_logfile))
        if new_logfile.exists():
            new_logfile.unlink()
        self.logfile.rename(new_logfile)

    @step
    def kill_instance(self):
        """ terminate the process represented by this wrapper class """
        if self.instance:
            try:
                print('force-killing {0} instance PID:[{1}]'.format(
                    self.type_str,
                    self.instance.pid))
                self.instance.kill()
                # if the starter is stopped, will never end:
                # self.instance.wait()
            except psutil.NoSuchProcess:
                logging.info("instance already dead: " + str(self.instance))
            self.instance = None
        else:
            logging.info("I'm already dead, jim!" + str(repr(self)))

    @step
    def terminate_instance(self, add_logfile_to_report=True):
        """ terminate the process represented by this wrapper class """
        if self.instance:
            try:
                print('terminating {0} instance PID:[{1}]'.format(
                    self.type_str,
                    self.instance.pid))
                self.instance.terminate()
                self.instance.wait()
                if add_logfile_to_report:
                    self.add_logfile_to_report()
            except psutil.NoSuchProcess:
                logging.info("instance already dead: " + str(self.instance))
            self.instance = None
        else:
            logging.info("I'm already dead, jim!" + str(repr(self)))

    @step
    def suspend_instance(self):
        """ halt an instance using SIG_STOP """
        if self.instance:
            try:
                print('suspending {0} instance PID:[{1}]'.format(
                    self.type_str,
                    self.instance.pid))
                self.instance.suspend()
            except psutil.NoSuchProcess as ex:
                logging.info("instance not available with this PID: " + str(self.instance))
                raise ex
        else:
            logging.error("instance not available with this PID: " + str(repr(self)))

    @step
    def resume_instance(self):
        """ resume the instance using SIG_CONT """
        if self.instance:
            try:
                print('resuming {0} instance PID:[{1}]'.format(
                    self.type_str,
                    self.instance.pid))
                self.instance.resume()
            except psutil.NoSuchProcess:
                logging.info("instance not available with this PID: " + str(self.instance))
            self.instance = None
        else:
            logging.error("instance not available with this PID: " + str(repr(self)))

    @step
    def crash_instance(self):
        """ send SIG-11 to instance... """
        if self.instance:
            try:
                print(self.instance.status() )
                if (self.instance.status() == psutil.STATUS_RUNNING or
                    self.instance.status() == psutil.STATUS_SLEEPING):
                    print("generating coredump for " + str(self.instance))
                    gcore = psutil.Popen(['gcore', str(self.instance.pid)], cwd=self.basedir)
                    print("generating core with PID:" + str(gcore.pid))
                    gcore.wait()
                    print('Killing {0} instance PID:[{1}] {3}'.format(
                        self.type_str,
                        self.instance.pid,
                        self.instance.cmdline()))
                    self.instance.kill()
                    self.instance.wait()
                    self.add_logfile_to_report()
                else:
                    print("NOT generating coredump for " + str(self.instance))
            except psutil.NoSuchProcess:
                logging.info("instance already dead: " + str(self.instance))
            self.instance = None
        else:
            logging.info("I'm already dead, jim!" + str(repr(self)))

    @step
    def wait_for_shutdown(self):
        """ wait for the instance to anounce its dead! """
        while True:
            try:
                psutil.Process(self.pid)
                time.sleep(0.1)
            except psutil.NoSuchProcess:
                break

    def get_endpoint(self):
        """ arangodb enpoint - to be specialized (if) """
        raise Exception("this instance doesn't support endpoints." + repr(self))

    def is_suppressed_log_line(self, line):
        """ check whether this is one of the errors we can ignore """
        for blacklist_item in LOG_BLACKLIST:
            if blacklist_item in line:
                return True
        if self.is_system:
            for blacklist_item in LOG_SYSTEM_BLACKLIST:
                if blacklist_item in line:
                    return True
        return False

    def is_line_relevant(self, line):
        """ it returns true if the line from logs should be printed """
        # pylint: disable=R0201
        return "FATAL" in line or "ERROR" in line or "WARNING" in line or "{crash}" in line

    def search_for_warnings(self):
        """ browse our logfile for warnings and errors """
        if not self.logfile.exists():
            print(str(self.logfile) + " doesn't exist, skipping.")
            return
        print(str(self.logfile))
        count = 0
        with open(self.logfile, errors='backslashreplace') as log_fh:
            for line in log_fh:
                if self.is_line_relevant(line):
                    if self.is_suppressed_log_line(line):
                        count += 1
                    else:
                        print(line.rstrip())
        if count > 0:
            print(" %d lines suppressed by filters" % count)

    @step
    def add_logfile_to_report(self):
        """ Add log to allure report"""
        logfile = str(self.logfile)
        attach.file(logfile,
                    "Log file(name: {name}, PID:{pid}, port: {port}, type: {type})"
                    .format(name=self.name, pid=self.pid, port=self.port, type=self.type_str),
                    AttachmentType.TEXT)


class ArangodInstance(Instance):
    """ represent one arangodb instance """
    # pylint: disable=R0913
    def __init__(self, typ, port, localhost, publicip, basedir, passvoid, ssl, is_system=False):
        super().__init__(typ,
                         port,
                         basedir,
                         localhost,
                         publicip,
                         passvoid,
                         'arangod',
                         ssl)
        self.is_system = is_system

    def __repr__(self):
        # raise Exception("blarg")
        return """
 {0.name}  |  {0.type_str}  | {0.pid} | {0.logfile}
""".format(self)

    def get_uuid(self):
        """ try to load the instances UUID """
        uuid_file = self.basedir / 'data' / 'UUID'
        return uuid_file.read_text()

    def get_essentials(self):
        """ get the essential attributes of the class """
        return {
            "name": self.name,
            "pid": self.pid,
            "type": self.type_str,
            "log": self.logfile,
            "is_frontend": self.is_frontend(),
            "url": self.get_public_login_url() if self.is_frontend() else ""
        }

    # pylint: disable=R1705
    def get_protocol(self):
        """ return protocol of this arangod instance (ssl/tcp) """
        if self.ssl:
            return "ssl"
        else:
            return "tcp"

    # pylint: disable=R1705
    def get_http_protocol(self):
        """ return protocol of this arangod instance (http/https) """
        if self.ssl:
            return "https"
        else:
            return "http"

    def get_local_url(self, login):
        """ our local url """
        return '{protocol}://{login}{host}:{port}'.format(
            protocol=self.get_http_protocol(),
            login=login,
            host=self.localhost,
            port=self.port)

    def get_public_url(self, login):
        """ our public url """
        return '{protocol}://{login}{host}:{port}'.format(
            protocol=self.get_http_protocol(),
            login=login,
            host=self.publicip,
            port=self.port)

    def get_public_login_url(self):
        """ our public url with passvoid """
        return '{protocol}://root:{passvoid}@{publicip}:{port}'.format(
            protocol = self.get_http_protocol(),
            passvoid = self.passvoid,
            publicip=self.publicip,
            port=self.port
        )

    def get_public_plain_url(self):
        """ our public url """
        return '{host}:{port}'.format(
            host=self.publicip,
            port=self.port)

    def get_endpoint(self):
        """ our endpoint """
        return '{protocol}://{host}:{port}'.format(
            protocol=self.get_protocol(),
            host=self.localhost,
            port=self.port)

    def is_frontend(self):
        """ is this instance a frontend """
        # print(repr(self))
        return self.instance_type in [
            InstanceType.COORDINATOR,
            InstanceType.RESILIENT_SINGLE,
            InstanceType.SINGLE]

    def is_dbserver(self):
        """ is this instance a dbserver? """
        return self.instance_type in [
            InstanceType.DBSERVER,
            InstanceType.RESILIENT_SINGLE,
            InstanceType.SINGLE]

    def is_sync_instance(self):
        """ no. """
        # pylint: disable=R0201
        return False

    @step
    def wait_for_logfile(self, tries):
        """ wait for logfile to appear """
        while not self.logfile.exists() and tries:
            progress(':')
            time.sleep(1)
            tries -= 1

    def probe_if_is_leader(self):
        """ detect if I am the leader? """
        return self.get_afo_state() == AfoServerState.LEADER

    @step
    def check_version_request(self, timeout):
        """ wait for the instance to reply with 200 to api/version """
        until = time.time() + timeout
        while until < time.time():
            reply = None
            try:
                reply = requests.get(self.get_local_url('')+'/_api/version')
                if reply.status_code == 200:
                    return
                print('*')
            except requests.exceptions.ConnectionError:
                print('&')
            time.sleep(0.5)

    def get_afo_state(self):
        """ is this a leader or follower? """
        reply = None
        try:
            reply = requests.get(self.get_local_url('')+'/_api/version',
                                 auth=HTTPBasicAuth('root', self.passvoid),
                                 verify = False
                                 )
        except requests.exceptions.ConnectionError:
            return AfoServerState.NOT_CONNECTED

        if reply.status_code == 200:
            return AfoServerState.LEADER
        if reply.status_code == 503:
            body_json = json.loads(reply.content)
            # leadership challenge is ongoing...
            if body_json['errorNum'] == 1495:
                return AfoServerState.CHALLENGE_ONGOING
            # leadership challenge is ongoing...
            if body_json['errorNum'] == 1496:
                return AfoServerState.NOT_LEADER
            if body_json['errorNum'] == 503:
                return AfoServerState.STARTUP_MAINTENANCE
            raise Exception("afo_state: unsupported error code in "
                            + str(reply.content))
        raise Exception("afo_state: unsupportet HTTP-Status code "
                        + str(reply.status_code) + str(reply))

    def detect_restore_restart(self):
        """ has the server restored their backup restored and is back up """
        logging.debug("scanning " + str(self.logfile))
        while True:
            log_file_content = ""
            last_line = ''
            with open(self.logfile, errors='backslashreplace') as log_fh:
                for line in log_fh:
                    # skip empty lines
                    if line == "":
                        continue
                    # save last line and append to string
                    # (why not slurp the whole file?)
                    last_line = line
                    log_file_content += '\n' + line

            # check last line or continue
            match = re.search(r'Z \[(\d*)\]', last_line)
            if match is None:
                logging.info("no PID in: %s", last_line)
                continue

            # pid found now find the position of the pid in
            # the logfile and check it is followed by a
            # ready for business.
            pid = match.groups()[0]
            start = log_file_content.find(pid)

            offset = log_file_content.find(
                'RocksDBHotBackupRestore:  restarting server with restored data',
                start)
            if offset >= 0:
                print("server restarting with restored backup.")
                self.detect_pid(0, offset)
                if self.instance_type == InstanceType.RESILIENT_SINGLE:
                    print("waiting for leader election: ", end="")
                    status = AfoServerState.CHALLENGE_ONGOING
                    while status in [AfoServerState.CHALLENGE_ONGOING,
                                     AfoServerState.NOT_CONNECTED,
                                     AfoServerState.STARTUP_MAINTENANCE]:
                        status = self.get_afo_state()
                        progress('%')
                        time.sleep(0.1)
                    print()
                return
            progress(',')
            time.sleep(0.1)

    def detect_fatal_errors(self):
        """ check whether we have FATAL lines in the logfile """
        fatal_line = None
        with open(self.logfile, errors='backslashreplace') as log_fh:
            for line in log_fh:
                if fatal_line is not None:
                    fatal_line += "\n" + line
                elif "] FATAL [" in line:
                    fatal_line = line

        if fatal_line is not None:
            print('Error: ', fatal_line)
            raise Exception("FATAL error found in " + str(self.logfile) + ": " + fatal_line)

    def detect_pid(self, ppid, offset=0, full_binary_path=""):
        """ detect the instance """
        # pylint: disable=R0915 disable=R0914
        self.pid = 0
        self.ppid = ppid
        tries = 40
        t_start = ''
        while self.pid == 0 and tries:

            log_file_content = ''
            last_line = ''

            for _ in range(20):
                if self.logfile.exists():
                    break
                time.sleep(1)
            else:
                raise TimeoutError("instance logfile '" +
                                   str(self.logfile) +
                                   "' didn't show up in 20 seconds")

            with open(self.logfile, errors='backslashreplace') as log_fh:
                for line in log_fh:
                    # skip empty lines
                    if line == "":
                        time.sleep(1)
                        continue
                    if "] FATAL [" in line and not self.is_suppressed_log_line(line):
                        print('Error: ', line)
                        raise Exception("FATAL error found in " +
                                        str(self.logfile) +
                                        ": " + line)
                    # save last line and append to string
                    # (why not slurp the whole file?)
                    last_line = line
                    log_file_content += '\n' + line

            # check last line or continue
            match = re.search(r'Z \[(\d*)\]', last_line)
            if match is None:
                tries -=1
                logging.info("no PID in [%s]: %s", self.logfile, last_line)
                progress('.')
                time.sleep(1)
                continue

            # pid found now find the position of the pid in
            # the logfile and check it is followed by a
            # ready for business.
            pid = match.groups()[0]
            start = log_file_content.find(pid, offset)
            ready_for_business = 'is ready for business.'
            pos = log_file_content.find(ready_for_business, start)
            if pos < 0:
                tries -=1
                progress('.')
                time.sleep(1)
                continue
            self.pid = int(pid)
            # locate the timestamp of our 'ready for business' line:
            match = re.search(r'(.*)Z \['+pid+'].*' + ready_for_business,
                              log_file_content[pos - 140:])
            if match is None:
                tries -=1
                self.pid = 0
                print('ny' * 40)
                print(log_file_content[pos - 140:])
                print(log_file_content)
                print(pos)
                time.sleep(1)
                progress('.')
                continue

            t_start = match.group(1)
            logging.debug(
                "found pid {0} for instance with logfile {1} at {2}.".format(
                self.pid,
                str(self.logfile),
                t_start
            ))
            try:
                self.instance = psutil.Process(self.pid)
            except psutil.NoSuchProcess:
                logging.info("process for PID:%d already gone? retrying.",
                             self.pid)
                time.sleep(1)
                self.pid = 0  # a previous log run? retry.
            time.sleep(1)
            progress(':')

        if self.pid == 0:
            print()
            logging.error("could not get pid for instance: " + repr(self))
            logging.error("inspect: " + str(self.logfile))
            raise TimeoutError("could not get pid for instance: " + repr(self))
        logging.info(
            "found process for pid {0} for "
            "instance with logfile {1} at {2}.".format(
                self.pid,
                str(self.logfile),
                t_start
            ))

    def search_for_agent_serving(self):
        """ this string is emitted by the agent, if he is leading the agency:
 2021-05-19T16:02:18Z [3447] INFO [a66dc] {agency} AGNT-0dc4dd67-4340-4645-913f-9415adfbeda7
   rebuilt key-value stores - serving.
        """
        serving_line = None
        if not self.logfile.exists():
            print(str(self.logfile) + " doesn't exist, skipping.")
            return self.serving
        with open(self.logfile, errors='backslashreplace') as log_fh:
            for line in log_fh:
                if 'a66dc' in line:
                    serving_line = line
        if serving_line:
            self.serving = log_line_get_date(serving_line)
        return self.serving

class ArangodRemoteInstance(ArangodInstance):
    """ represent one arangodb instance """
    # pylint: disable=R0913
    def __init__(self, typ, port, localhost, publicip, basedir, passvoid, ssl):
        super().__init__(typ,
                         port,
                         basedir,
                         localhost,
                         publicip,
                         passvoid,
                         'arangod',
                         ssl)

class SyncInstance(Instance):
    """ represent one arangosync instance """
    # pylint: disable=R0913
    def __init__(self, typ, port, localhost, publicip, basedir, passvoid, ssl):
        super().__init__(typ,
                         port,
                         basedir,
                         localhost,
                         publicip,
                         passvoid,
                         'arangosync',
                          ssl)
        self.logfile_parameter = ''

    def __repr__(self):
        """ dump us """
        #raise Exception("blarg")
        return """
 arangosync instance | type  | pid  | logfile
       {0.name}      | {0.type_str} |  {0.pid} |  {0.logfile}
 """.format(self)

    def get_essentials(self):
        """ get the essential attributes of the class """
        return {
            "name": self.name,
            "pid": self.pid,
            "type": self.type_str,
            "log": self.logfile,
            "is_frontend": False,
            "url": ""
        }
    def analyze_starter_file_line(self, line):
        if line.find('--log.file') >=0:
            self.logfile_parameter = line

    def detect_pid(self, ppid, offset, full_binary_path):
        # first get the starter provided commandline:
        self.ppid = ppid
        self.load_starter_instance_control_file()
        logfile_parameter_raw = ''
        if self.logfile_parameter == '--log.file':
            # newer starters will use '--foo bar' instead of '--foo=bar'
            logfile_parameter_raw = self.instance_arguments[
                self.instance_arguments.index('--log.file') + 1]
            self.logfile_parameter = "--log.file=" + logfile_parameter_raw
        else:
            logfile_parameter_raw = self.logfile_parameter.split('=')[1]
        # wait till the process has startet writing its logfile:
        while not self.logfile.exists():
            progress('v')
            time.sleep(1)
        possible_me_pid = []
        count = 0
        while count < 300 and len(possible_me_pid) == 0:
            for process in psutil.process_iter():
                if process.ppid() == ppid and process.name() == 'arangosync':
                    proccmd = process.cmdline()[1:]
                    try:
                        # this will throw if its not in there:
                        proccmd.index(self.logfile_parameter)
                        possible_me_pid.append({
                            'p': process.pid,
                            'cmdline': proccmd
                        })
                    except ValueError:
                        try:
                            # this will throw if its not in there:
                            proccmd.index(logfile_parameter_raw)
                            possible_me_pid.append({
                                'p': process.pid,
                                'cmdline': proccmd
                            })
                        except ValueError:
                            pass

            if len(possible_me_pid) == 0 and count > 0:
                progress('s')
                time.sleep(1)
            count += 1

        if len(possible_me_pid) != 1:
            raise Exception("wasn't able to identify my arangosync process! "
                            + str(possible_me_pid))
        self.pid = possible_me_pid[0]['p']
        self.instance = psutil.Process(self.pid)

    def wait_for_logfile(self, tries):
        """ not implemented """

    def is_frontend(self):
        """ no. """
        # pylint: disable=R0201
        return False

    def is_dbserver(self):
        """ no. """
        # pylint: disable=R0201
        return False

    def is_sync_instance(self):
        """ yes. """
        # pylint: disable=R0201
        return True

    def is_line_relevant(self, line):
        """ it returns true if the line from logs should be printed """
        if ("|FATAL|" in line or "|ERRO|" in line or "|WARN|" in line):
            # logs from arangosync v1
            return True
        if (" FTL " in line or " ERR " in line or " WRN " in line):
            # logs from arangosync v2
            return True

        return False

    def get_public_plain_url(self):
        """ get the public connect URL """
        return '{host}:{port}'.format(
            host=self.publicip,
            port=self.port)

def get_instances_table(instances):
    """ print all instances provided in tabular format """
    table = BeautifulTable(maxwidth=160)
    for one_instance in instances:
        table.rows.append([
            one_instance["name"],
            one_instance["pid"],
            one_instance["type"],
            one_instance["log"],
            # one_instance["is_frontend"],
            one_instance["url"]
            ])
    table.columns.header = [
        "Name",
        "PID",
        "type",
        "Logfile",
        # "Frontend",
        "URL"
    ]
    return table

def print_instances_table(instances):
    """ print all instances provided in tabular format """
    table = get_instances_table(instances)
    print(str(table))
    attach_table(table, "Instances table")
