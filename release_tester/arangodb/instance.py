#!/usr/bin/env python3
""" class to manage an arangod or arangosync instance """
from abc import abstractmethod, ABC
from enum import IntEnum
import json
import logging
import re
import sys
import time
import requests

import psutil
from tools.asciiprint import print_progress as progress


class InstanceType(IntEnum):
    """ type of arangod instance """
    coordinator = 1
    resilientsingle = 2
    single = 3
    agent = 4
    dbserver = 5
    syncmaster = 6
    syncworker = 7


TYP_STRINGS = ["none", "none",
               "coordinator"
               "resilientsingle",
               "single",
               "agent",
               "dbserver",
               "syncmaster",
               "syncworker"]

class AfoServerState(IntEnum):
    """ in which sate is this active failover instance? """
    leader = 1
    not_leader = 2
    challenge_ongoing = 3
    startup_maintainance = 4
    not_connected = 5

class Instance(ABC):
    """abstract instance manager"""
    # pylint: disable=R0913 disable=R0902
    def __init__(self, typ, port, basedir, localhost, publicip, logfile):
        self.type = InstanceType[typ]  # convert to enum
        self.type_str = TYP_STRINGS[int(self.type.value)]
        self.port = port
        self.pid = None
        self.basedir = basedir
        self.logfile = logfile
        self.localhost = localhost
        self.publicip = publicip
        self.name = self.type.name + str(self.port)
        self.instance = None
        logging.debug("creating {0.type_str} instance: {0.name}".format(self))

    @abstractmethod
    def detect_pid(self, ppid, offset, full_binary_path):
        """ gets the PID from the running process of this instance """

    def detect_gone(self):
        """ revalidate that the managed process is actualy dead """
        try:
            # we expect it to be dead anyways!
            return self.instance.wait(3) is None
        except psutil.TimeoutExpired:
            logging.error("was supposed to be dead, but I'm still alive? "
                          + repr(self))
            return True

    def rename_logfile(self):
        """ to ease further analysis, move old logfile out of our way"""
        logfile = str(self.logfile)
        logging.info("renaming instance logfile: %s -> %s",
                     logfile, logfile + '.old')
        self.logfile.rename(logfile + '.old')

    def terminate_instance(self):
        """ terminate the process represented by this wrapper class """
        if self.instance:
            try:
                self.instance.terminate()
                self.instance.wait()
            except psutil.NoSuchProcess:
                logging.info("instance already dead: " + str(self.instance))
            self.instance = None
        else:
            logging.info("I'm already dead, jim!" + str(repr(self)))

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

class ArangodInstance(Instance):
    """ represent one arangodb instance """
    # pylint: disable=R0913
    def __init__(self, typ, port, localhost, publicip, basedir):
        super().__init__(typ,
                         port,
                         basedir,
                         localhost,
                         publicip,
                         basedir / 'arangod.log')

    def __repr__(self):
        return """
arangod instance
    name:    {0.name}
    type:    {0.type_str}
    pid:     {0.pid}
    logfile: {0.logfile}
""".format(self)

    def get_local_url(self, login):
        """ our public url """
        return 'http://{login}{host}:{port}'.format(
            login=login,
            host=self.localhost,
            port=self.port)

    def get_public_url(self, login):
        """ our public url """
        return 'http://{login}{host}:{port}'.format(
            login=login,
            host=self.publicip,
            port=self.port)

    def get_public_plain_url(self):
        """ our public url """
        return '{host}:{port}'.format(
            host=self.publicip,
            port=self.port)

    def get_endpoint(self):
        """ our endpoint """
        return 'tcp://{host}:{port}'.format(
            host=self.localhost,
            port=self.port)

    def is_frontend(self):
        """ is this instance a frontend """
        # print(repr(self))
        return self.type in [InstanceType.coordinator,
                             InstanceType.resilientsingle,
                             InstanceType.single]

    def is_dbserver(self):
        """ is this instance a dbserver? """
        return self.type in [InstanceType.dbserver,
                             InstanceType.resilientsingle,
                             InstanceType.single]

    def is_sync_instance(self):
        """ no. """
        # pylint: disable=R0201
        return False

    def wait_for_logfile(self, tries):
        """ wait for logfile to appear """
        while not self.logfile.exists() and tries:
            progress(':')
            time.sleep(1)
            tries -= 1

    def probe_if_is_leader(self):
        """ detect if I am the leader? """
        return self.get_afo_state() == AfoServerState.leader

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
            reply = requests.get(self.get_local_url('')+'/_api/version')
        except requests.exceptions.ConnectionError:
            return AfoServerState.not_connected

        if reply.status_code == 200:
            return AfoServerState.leader
        if reply.status_code == 503:
            body_json = json.loads(reply.content)
            # leadership challenge is ongoing...
            if body_json['errorNum'] == 1495:
                return AfoServerState.challenge_ongoing
            # leadership challenge is ongoing...
            if body_json['errorNum'] == 1496:
                return AfoServerState.not_leader
            if body_json['errorNum'] == 503:
                return AfoServerState.startup_maintainance
            raise Exception("afo_state: unsupported error code in "
                            + str(reply.content))
        raise Exception("afo_state: unsupportet HTTP-Status code "
                        + str(reply.status_code))

    def detect_restore_restart(self):
        """ has the server restored their backup restored and is back up """
        logging.debug("scanning " + str(self.logfile))
        while True:
            log_file_content = ""
            last_line = ''
            with open(self.logfile) as log_fh:
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
                if self.type == InstanceType.resilientsingle:
                    print("waiting for leader election: ", end="")
                    status = AfoServerState.challenge_ongoing
                    while status in [AfoServerState.challenge_ongoing,
                                     AfoServerState.not_connected,
                                     AfoServerState.startup_maintainance]:
                        status = self.get_afo_state()
                        progress('%')
                        time.sleep(0.1)
                    print()
                return
            progress(',')
            time.sleep(0.1)

    def detect_pid(self, ppid, offset=0, full_binary_path=""):
        """ detect the instance """
        self.pid = 0
        tries = 20
        t_start = ''
        while self.pid == 0 and tries:

            log_file_content = ''
            last_line = ''

            with open(self.logfile) as log_fh:
                for line in log_fh:
                    # skip empty lines
                    if line == "":
                        continue
                    if "] FATAL [" in line:
                        print('Error: ', line)
                        raise Exception("FATAL error found in arangod.log.")
                    # save last line and append to string
                    # (why not slurp the whole file?)
                    last_line = line
                    log_file_content += '\n' + line

            # check last line or continue
            match = re.search(r'Z \[(\d*)\]', last_line)
            if match is None:
                logging.info("no PID in [%s]: %s", self.logfile, last_line)
                continue

            # pid found now find the position of the pid in
            # the logfile and check it is followed by a
            # ready for business.
            pid = match.groups()[0]
            start = log_file_content.find(pid, offset)
            ready_for_business = 'is ready for business.'
            pos = log_file_content.find(ready_for_business, start)
            if pos < 0:
                progress('.')
                time.sleep(1)
                continue
            self.pid = int(pid)
            # locate the timestamp of our 'ready for business' line:
            match = re.search(r'(.*)Z \['+pid+'].*' + ready_for_business,
                              log_file_content[pos - 140:])
            if match is None:
                tries -=1
                print(log_file_content[pos - 140:])
                print(log_file_content)
                print(pos)
                time.sleep(1)
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
                logging.info("process for PID %d already gone? retrying.",
                             self.pid)
                time.sleep(1)
                self.pid = 0  # a previous log run? retry.
        if self.pid == 0:
            print()
            logging.error("could not get pid for instance: " + repr(self))
            logging.error("inspect: " + str(self.logfile))
            sys.exit(1)
        else:
            logging.info(
                "found process for pid {0} for "
                "instance with logfile {1} at {2}.".format(
                self.pid,
                str(self.logfile),
                t_start
            ))

class ArangodRemoteInstance(ArangodInstance):
    """ represent one arangodb instance """
    # pylint: disable=R0913
    def __init__(self, typ, port, localhost, publicip, basedir):
        super().__init__(typ, port, localhost, publicip, basedir)

class SyncInstance(Instance):
    """ represent one arangosync instance """
    # pylint: disable=R0913
    def __init__(self, typ, port, localhost, publicip, basedir):
        super().__init__(typ,
                         port,
                         basedir,
                         localhost,
                         publicip,
                         basedir / 'arangosync.log')

    def __repr__(self):
        """ dump us """
        return """
arangosync instance of starter
    name:    {0.name}
    type:    {0.type_str}
    pid:     {0.pid}
    logfile: {0.logfile}
""".format(self)

    def detect_pid(self, ppid, offset, full_binary_path):
        # first get the starter provided commandline:
        command = self.basedir / 'arangosync_command.txt'
        cmd = []
        # we search for the logfile parameter, since its unique to our instance.
        logfile_parameter = ''
        with open(command) as filedesc:
            for line in filedesc.readlines():
                line = line.rstrip().rstrip(' \\')
                if line.find('--log.file') >=0:
                    logfile_parameter = line
                cmd.append(line)
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
                        proccmd.index(logfile_parameter)
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
