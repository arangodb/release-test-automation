#!/usr/bin/env python3
""" class to manage an arangod or arangosync instance """
import logging
import re
from abc import abstractmethod, ABC
from enum import Enum
import sys
import time
import requests
import json

import psutil


class InstanceType(Enum):
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

class AfoServerState(Enum):
    leader = 1
    not_leader = 2
    challenge_ongoing = 3
    not_connected = 4

class Instance(ABC):
    """abstract instance manager"""
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
    def detect_pid(self, ppid):
        """ gets the PID from the running process of this instance """

    def detect_gone(self):
        """ revalidate that the managed process is actualy dead """
        try:
            return self.instance.wait(3) is None  # we expect it to be dead anyways!
        except:
            logging.error("was supposed to be dead, but I'm still alive? " + repr(self))
            return True

    def rename_logfile(self):
        """ to ease further analysis, move old logfile out of our way"""
        logfile = str(self.logfile)
        logging.info("renaming instance logfile: %s -> %s", logfile, logfile + '.old')
        self.logfile.rename(logfile + '.old')

    def terminate_instance(self):
        self.instance.terminate()
        self.instance.wait()


class ArangodInstance(Instance):
    """ represent one arangodb instance """
    def __init__(self, typ, port, localhost, publicip, basedir):
        super().__init__(typ, port, basedir, localhost, publicip, basedir / 'arangod.log')

    def __repr__(self):
        return """
arangod instance
    name:    {0.name}
    type:    {0.type_str}
    pid:     {0.pid}
    logfile: {0.logfile}
""".format(self)

    def get_local_url(self, login):
        return 'http://{login}{host}:{port}'.format(
            login=login,
            host=self.localhost,
            port=self.port)

    def get_public_url(self, login):
        return 'http://{login}{host}:{port}'.format(
            login=login,
            host=self.publicip,
            port=self.port)

    def get_public_plain_url(self):
        return '{host}:{port}'.format(
            host=self.publicip,
            port=self.port)

    def is_frontend(self):
        """ is this instance a frontend """
        # print(repr(self))
        if self.type in [InstanceType.coordinator,
                         InstanceType.resilientsingle,
                         InstanceType.single]:
            return True
        else:
            return False

    def is_dbserver(self):
        """ is this instance a dbserver? """
        if self.type in [InstanceType.dbserver,
                         InstanceType.resilientsingle,
                         InstanceType.single]:
            return True
        else:
            return False

    def is_sync_instance(self):
        return False

    def wait_for_logfile(self, tries):
        """ wait for logfile to appear """
        while not self.logfile.exists() and tries:
            print(':')
            time.sleep(1)
            tries -= 1

    def probe_if_is_leader(self):
        return self.get_afo_state() == AfoServerState.leader

    def get_afo_state(self):
        reply = None
        try:
            reply = requests.get(self.get_local_url('')+'/_api/version')
        except requests.exceptions.ConnectionError as x:
            return AfoServerState.not_connected

        if reply.status_code == 200:
            return AfoServerState.leader
        elif reply.status_code == 503:
            body_json = json.loads(reply.content)
            if body_json['errorNum'] == 1495: # leadership challenge is ongoing...
                return AfoServerState.challenge_ongoing
            elif body_json['errorNum'] == 1496: # leadership challenge is ongoing...
                return AfoServerState.not_leader
            else:
                raise Exception("afo_state: unsupported error code in " + str(reply.content))
        else:
            raise Exception("afo_state: unsupportet HTTP-Status code " + str(reply.status_code))

    def detect_restore_restart(self):
        while True:
            log_file_content = ""
            last_line = ''
            with open(self.logfile) as log_fh:
                for line in log_fh:
                    # skip empty lines
                    if line == "":
                        continue
                    # save last line and append to string (why not slurp the whole file?)
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
                    while status is AfoServerState.challenge_ongoing or status is AfoServerState.not_connected:
                        status = self.get_afo_state()
                        print('%', end='')
                        time.sleep(0.1)
                    print()
                return
            print(',', end="")
            time.sleep(0.1)

    def detect_pid(self, ppid, offset=0):
        """ detect the instance """
        self.pid = 0
        tries = 20
        tStart = ''
        while self.pid == 0 and tries:

            log_file_content = ''
            last_line = ''

            with open(self.logfile) as log_fh:
                for line in log_fh:
                    # skip empty lines
                    if line == "":
                        continue
                    # save last line and append to string (why not slurp the whole file?)
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
            start = log_file_content.find(pid, offset)
            ready_for_business = 'is ready for business.'
            pos = log_file_content.find(ready_for_business, start)
            if pos < 0:
                print('.', end='')
                sys.stdout.flush()
                time.sleep(1)
                continue
            self.pid = int(pid)
            # locate the timestamp of our 'ready for business' line:
            match = re.search(r'(.*)Z \['+pid+'].*' + ready_for_business,
                              log_file_content[pos - 90:])
            tStart = match.group(1)
            logging.debug("found pid {0} for instance with logfile {1} at {2}.".format(
                self.pid,
                str(self.logfile),
                tStart
            ))
            try:
                self.instance = psutil.Process(self.pid)
            except psutil.NoSuchProcess:
                logging.info("process for PID %d already gone? retrying.", self.pid)
                time.sleep(1)
                self.pid = 0  # a previous log run? retry.
        if self.pid == 0:
            print()
            logging.error("could not get pid for instance: " + repr(self))
            logging.error("inspect: " + str(self.logfile))
            sys.exit(1)
        else:
            logging.info("found process for pid {0} for instance with logfile {1} at {2}.".format(
                self.pid,
                str(self.logfile),
                tStart
            ))


class SyncInstance(Instance):
    """ represent one arangosync instance """
    def __init__(self, typ, port, localhost, publicip, basedir):
        super().__init__(typ, port, basedir, localhost, publicip, basedir / 'arangosync.log')

    def __repr__(self):
        return """
arangosync instance of starter
    name:    {0.name}
    type:    {0.type_str}
    pid:     {0.pid}
    logfile: {0.logfile}
""".format(self)

    def detect_pid(self, ppid):
        # first get the starter provided commandline:
        command = self.basedir / 'arangosync_command.txt'
        cmd = []
        with open(command) as f:
            for line in f.readlines():
                cmd.append(line.rstrip().rstrip(' \\'))
        # wait till the process has startet writing its logfile:
        while not self.logfile.exists():
            print('v')
            time.sleep(1)
        possible_me_pid = []
        for p in psutil.process_iter():
            if p.ppid() == ppid:
                proccmd = p.cmdline()
                if len(set(proccmd) & set(cmd)) == len(cmd):
                    possible_me_pid.append({
                        'p': p.pid,
                        'cmdline': proccmd
                    })
        if len(possible_me_pid) != 1:
            raise("wasn't able to identify my arangosync process! " + str(possible_me_pid))
        self.pid = possible_me_pid[0]['p']
        self.instance = psutil.Process(self.pid)

    def wait_for_logfile(self, tries):
        pass

    def is_frontend(self):
        return False

    def is_dbserver(self):
        return False

    def is_sync_instance(self):
        return True
