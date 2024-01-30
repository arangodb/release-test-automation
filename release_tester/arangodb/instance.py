#!/usr/bin/env python3
""" class to manage an arangod or arangosync instance """
# pylint: disable=too-many-lines
import datetime
import json
import logging
import os
import platform
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
from tools.utils import COLUMN_CACHE_ARGUMENT, is_column_cache_supported

# log tokens we want to suppress from our dump:
LOG_BLACKLIST = [
    "2b6b3",  # -> asio error, tcp connections died... so f* waht.
    "2c712",  # -> agency connection died...
    "40e37",  # -> upgrade required TODO remove me from here, add system instance handling.
    "d72fb",  # -> license is going to expire...
    "1afb1",  # -> unlicensed enterprise instance
    "9afd3",  # -> Warning while instantiation of icu::Collator
#     "32781",  # -> BTS-1263 - starter launches instances before the agency is ready
    "7e050",  # -> heartbeat could not connect to agency endpoints
    "3e342",  # -> option has been renamed
    "2c0c6",  # -> extended names
    "de8f3",  # -> extended names
]
LOG_MAINTAINER_BLACKLIST = [  # if we use the 'source'-Distribution, these are expected:
    "0458b",  # -> maintainer version binary
    "bd666",  # -> maintainer version binary
]
FATAL_BLACKLIST = [
    # Next line is disabled to collect more data about the issue:
    # "11ca3",  # -> SIGTERM received during shutdown sequence GT-541
]
# log tokens we ignore in system ugprades...
LOG_SYSTEM_BLACKLIST = ["40e37"]  # -> upgrade required
IS_WINDOWS = bool(platform.win32_ver()[0])
IS_MAC = bool(platform.mac_ver()[0] != "")


class InstanceType(IntEnum):
    """type of arangod instance"""

    COORDINATOR = 0
    RESILIENT_SINGLE = 1
    SINGLE = 2
    AGENT = 3
    DBSERVER = 4
    SYNCMASTER = 5
    SYNCWORKER = 6


INSTANCE_TYPE_STRING_MAP = {
    "coordinator": InstanceType.COORDINATOR,
    "resilientsingle": InstanceType.RESILIENT_SINGLE,
    "single": InstanceType.SINGLE,
    "agent": InstanceType.AGENT,
    "dbserver": InstanceType.DBSERVER,
    "syncmaster": InstanceType.SYNCMASTER,
    "syncworker": InstanceType.SYNCWORKER,
}


def log_line_get_date(line):
    """parse the date out of an arangod logfile line"""
    return datetime.datetime.strptime(line.split(" ")[0], "%Y-%m-%dT%H:%M:%SZ")


class AfoServerState(IntEnum):
    """in which sate is this active failover instance?"""

    LEADER = 1
    NOT_LEADER = 2
    CHALLENGE_ONGOING = 3
    STARTUP_MAINTENANCE = 4
    NOT_CONNECTED = 5


class Instance(ABC):
    """abstract instance manager"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=too-many-public-methods
    def __init__(
        self,
        instance_type,
        port,
        basedir,
        localhost,
        publicip,
        passvoid,
        instance_string,
        ssl,
        version,
        enterprise,
        jwt="",
    ):
        self.instance_type = INSTANCE_TYPE_STRING_MAP[instance_type]
        self.is_system = False
        self.type_str = list(INSTANCE_TYPE_STRING_MAP.keys())[int(self.instance_type.value)]
        self.port = port
        self.pid = None
        self.ppid = None
        self.basedir = basedir
        self.instance_string = instance_string
        self.logfile = basedir / (instance_string + ".log")
        self.instance_control_file = basedir / (instance_string + "_command.txt")
        self.localhost = localhost
        self.publicip = publicip
        self.passvoid = passvoid
        self.name = self.instance_type.name + str(self.port)
        self.instance = None
        self.serving = datetime.datetime(1970, 1, 1, 0, 0, 0)
        self.instance_arguments = []
        self.ssl = ssl
        self.version = version
        self.enterprise = enterprise
        self.logfiles = []
        self.jwt = jwt
        self.source_instance = False
        logging.debug("creating {0.type_str} instance: {0.name}".format(self))

    def get_structure(self):
        """return instance structure like testing.js does"""
        try:
            endpoint = self.get_endpoint()
        except NotImplementedError:
            endpoint = ""
        return {
            "name": self.name,
            "instanceRole": self.type_str,
            "message": "",
            "rootDir": str(self.basedir),
            "protocol": self.get_http_protocol(),
            "authHeaders": "",
            "restKeyFile": "",
            "agencyConfig": {},
            "upAndRunning": True,
            "suspended": False,
            "port": self.port,
            "url": self.get_public_url(),
            "endpoint": endpoint,
            "dataDir": str(self.basedir / "data"),
            "appDir": str(self.basedir / "apps"),
            "tmpDir": "",
            "logFile": str(self.logfile),
            "args": str(self.instance_arguments),
            "pid": self.pid,
            "JWT": "",
            "exitStatus": 0,
            "serverCrashedLocal": False,
            "passvoid": self.passvoid,
        }

    @abstractmethod
    def detect_pid(self, ppid, offset, full_binary_path):
        """gets the PID from the running process of this instance"""

    def set_passvoid(self, passvoid):
        """set the pw to connect to this instance"""
        self.passvoid = passvoid

    def get_passvoid(self):
        """retrieve the pw to connect to this instance"""
        return self.passvoid

    def detect_gone(self):
        """revalidate that the managed process is actualy dead"""
        try:
            # we expect it to be dead anyways!
            return self.instance.wait(3) is None
        except psutil.TimeoutExpired:
            return False
        except AttributeError:
            # logging.error("was supposed to be dead, but I don't have an instance? "
            #              + repr(self))
            return True
        return True

    @abstractmethod
    def get_essentials(self):
        """get the essential attributes of the class"""

    def analyze_starter_file_line(self, line):
        """instance specific analyzer function"""
        # pylint: disable=unnecessary-pass
        pass

    def load_starter_instance_control_file(self):
        """load & parse the <instance_string>_command.txt file of the starter"""
        count = 20
        # Here we check not only for file existance, but also for its size.
        # The assumption is that if file is bigger than a certain size, it has been written completely.
        while (
            not self.instance_control_file.exists() or not self.instance_control_file.stat().st_size > 300
        ) and count > 0:
            count -= 1
            print("Instance control file not yet there?" + str(self.instance_control_file))
            time.sleep(0.5)

        if not self.instance_control_file.exists():
            raise FileNotFoundError("Instance control file not found! " + str(self.instance_control_file))
        if not self.instance_control_file.stat().st_size > 300:
            raise FileNotFoundError(
                "Instance control file is smaller than expected! " + str(self.instance_control_file)
            )
        self.instance_arguments = []
        with self.instance_control_file.open(errors="backslashreplace") as filedesc:
            for line in filedesc.readlines():
                if line.startswith("#"):
                    continue
                line = line.rstrip().rstrip(" \\")
                if line.find("build/bin") >= 0:
                    print("Source instance!")
                    self.source_instance = True
                if len(line) > 0:
                    self.analyze_starter_file_line(line)
                    self.instance_arguments.append(line)

    # pylint: disable=too-many-locals
    def launch_manual_from_instance_control_file(
        self, sbin_dir, old_install_prefix, new_install_prefix, current_version, enterprise, moreargs, waitpid=True
    ):
        """launch instance without starter with additional arguments"""
        self.load_starter_instance_control_file()
        command = [str(sbin_dir / self.instance_string)] + self.instance_arguments[1:] + moreargs
        dos_old_install_prefix_fwd = str(old_install_prefix).replace("\\", "/")
        dos_new_install_prefix_fwd = str(new_install_prefix).replace("\\", "/")

        is_cache_supported = is_column_cache_supported(current_version) and enterprise
        # in 'command' list arguments and values are splitted
        cache_arg, cache_val = COLUMN_CACHE_ARGUMENT.split("=")
        cache_arg = "--" + cache_arg[11:]  # remove '--args.all' prefix
        is_cache_arg_found = False
        for i, cmd in enumerate(command):
            if cmd.find(str(old_install_prefix)) >= 0:
                command[i] = cmd.replace(str(old_install_prefix), str(new_install_prefix))
            # the wintendo may have both slash directions:
            if cmd.find(dos_old_install_prefix_fwd) >= 0:
                command[i] = cmd.replace(dos_old_install_prefix_fwd, dos_new_install_prefix_fwd)
            if cmd == cache_arg:
                is_cache_arg_found = True
                if command[i + 1] != cache_val:
                    raise Exception("Something is wrong with ${COLUMN_CACHE_ARGUMENT}: ${command[i]} ${command[i+1]}")
                if not is_cache_supported:
                    del command[i + 1]
                    del command[i]

        if is_cache_supported and not is_cache_arg_found:
            command.append(cache_arg)
            command.append(cache_val)

        print("Manually launching: " + str(command))
        os.environ["ARANGODB_SERVER_DIR"] =  str(self.basedir)
        self.instance = psutil.Popen(command)
        del os.environ["ARANGODB_SERVER_DIR"]
        self.pid = self.instance.pid
        self.ppid = self.instance.ppid()

        print("instance launched with PID:" + str(self.pid))
        if waitpid:
            exception = None
            exit_code = None
            try:
                exit_code = self.instance.wait(timeout=300)
            except psutil.TimeoutExpired as ex:
                exception = ex
                print("timeout occured waiting for " + str(command))
            try:
                self.search_for_warnings()
            except Exception as ex:
                raise Exception(str(command) + " exited with code: " + str(exit_code)) from ex
            if exception is not None:
                raise exception
            if exit_code != 0:
                raise Exception(str(command) + " exited non zero: " + str(exit_code))

    @step
    def rename_logfile(self, suffix=".old"):
        """to ease further analysis, move old logfile out of our way"""
        number = len(self.logfiles) + 1
        logfile = str(self.logfile)
        old_logfile = Path(logfile + suffix + "." + str(number))
        msg = ""
        if old_logfile.exists():
            old_logfile.unlink()
            msg = "removed old"
        logging.info("renaming instance logfile: %s -> %s " + msg, logfile, str(old_logfile))
        self.logfile.rename(old_logfile)
        self.logfiles.append(old_logfile)

    @step
    def kill_instance(self):
        """terminate the process represented by this wrapper class"""
        if self.instance:
            print("force-killing {0} instance PID:[{1}]".format(self.type_str, self.instance.pid))
            self.instance.kill()

            self.instance = None
            self.pid = None
            self.ppid = None
        else:
            logging.info("I'm already dead, jim!" + str(repr(self)))

    @step
    def terminate_instance(self, add_logfile_to_report=True, force_kill_fatal=True):
        """terminate the process represented by this wrapper class"""
        if self.instance:
            try:
                print("terminating {0} instance PID:[{1}]".format(self.type_str, self.instance.pid))
                self.instance.terminate()
                self.instance.wait(600)
                if add_logfile_to_report:
                    self.add_logfile_to_report()
            except psutil.NoSuchProcess:
                logging.info("instance already dead: " + str(self.instance))
            except psutil.TimeoutExpired as exc:
                print("friendly terminating timed out, force killing:" + repr(self))
                self.kill_instance()
                if force_kill_fatal:
                    raise Exception("friendly shutdown of instance failed, did force kill") from exc

            self.instance = None
        else:
            logging.info("I'm already dead, jim!" + str(repr(self)))

    @step
    def suspend_instance(self):
        """halt an instance using SIG_STOP"""
        if self.instance:
            try:
                print("suspending {0} instance PID:[{1}]".format(self.type_str, self.instance.pid))
                self.instance.suspend()
            except psutil.NoSuchProcess as ex:
                logging.info("instance not available with this PID: " + str(self.instance))
                raise ex
        else:
            logging.error("instance not available with this PID: " + str(repr(self)))

    @step
    def resume_instance(self):
        """resume the instance using SIG_CONT"""
        if self.instance:
            try:
                print("resuming {0} instance PID:[{1}]".format(self.type_str, self.instance.pid))
                self.instance.resume()
            except psutil.NoSuchProcess:
                logging.info("instance not available with this PID: " + str(self.instance))
            self.instance = None
        else:
            logging.error("instance not available with this PID: " + str(repr(self)))

    @step
    def crash_instance(self):
        """send SIG-11 to instance..."""
        if self.instance:
            # try:
            print(self.instance.status())
            if self.instance.status() == psutil.STATUS_RUNNING or self.instance.status() == psutil.STATUS_SLEEPING:
                print("generating coredump for " + str(self.instance))
                gcore = psutil.Popen(["gcore", str(self.instance.pid)], cwd=self.basedir)
                print("generating core with PID:" + str(gcore.pid))
                gcore.wait()
                print(
                    "Killing {0} instance PID:[{1}] {3}".format(
                        self.type_str, self.instance.pid, self.instance.cmdline()
                    )
                )
                self.instance.kill()
                self.instance.wait()
                self.add_logfile_to_report()
            else:
                print("NOT generating coredump for " + str(self.instance))
            self.instance = None
        else:
            logging.info("I'm already dead, jim!" + str(repr(self)))

    @step
    def wait_for_shutdown(self):
        """wait for the instance to anounce its dead!"""
        while True:
            try:
                psutil.Process(self.pid)
                time.sleep(0.1)
            except psutil.NoSuchProcess:
                break

    def get_endpoint(self):
        """arangodb enpoint - to be specialized (if)"""
        raise NotImplementedError("this instance doesn't support endpoints." + repr(self))

    def is_suppressed_log_line(self, line):
        """check whether this is one of the errors we can ignore"""
        for blacklist_item in LOG_BLACKLIST:
            if blacklist_item in line:
                return True
        if self.source_instance:
            for blacklist_item in LOG_MAINTAINER_BLACKLIST:
                if blacklist_item in line:
                    return True
        if self.is_system:
            for blacklist_item in LOG_SYSTEM_BLACKLIST:
                if blacklist_item in line:
                    return True
        return False

    def is_line_relevant(self, line):
        """it returns true if the line from logs should be printed"""
        return "FATAL" in line or "ERROR" in line or "WARNING" in line or "{crash}" in line

    def is_line_fatal(self, line):
        """it returns true if the line from logs should be printed"""
        if "FATAL" in line or "{crash}" in line:
            for blacklist_item in FATAL_BLACKLIST:
                if blacklist_item in line:
                    return False
            return True
        return False

    def search_for_warnings(self, print_lines=True):
        """browse our logfile for warnings and errors"""
        count = 0
        ret = False
        for logfile in [self.logfile] + self.logfiles:
            if not logfile.exists():
                print(str(self.logfile) + " doesn't exist, skipping.")
            else:
                print(f"analyzing {str(logfile)}")
                with open(logfile, errors="backslashreplace", encoding="utf8") as log_fh:
                    for line in log_fh:
                        if self.is_line_relevant(line):
                            if self.is_line_fatal(line):
                                if print_lines:
                                    print(f"FATAL LINE FOUND: {line.rstrip()}")
                                ret = True
                            if self.is_suppressed_log_line(line):
                                count += 1
                            elif print_lines:
                                print(line.rstrip())
        if count > 0 and print_lines:
            print(" %d lines suppressed by filters" % count)
        return ret

    @step
    def add_logfile_to_report(self):
        """Add log to allure report"""
        if self.logfile is not None and self.logfile.exists():
            logfile = str(self.logfile)
            attach.file(
                logfile,
                "Log file(name: {name}, PID:{pid}, port: {port}, type: {type})".format(
                    name=self.name, pid=self.pid, port=self.port, type=self.type_str
                ),
                AttachmentType.TEXT,
            )
        else:
            step(f"Can't add log file because it doesn't exist: {str(self.logfile)}")

    # pylint: disable=no-else-return
    def get_http_protocol(self):
        """return protocol of this arangod instance (http/https)"""
        if self.ssl:
            return "https"
        else:
            return "http"

    def get_local_url(self, login):
        """our local url"""
        return "{protocol}://{login}{host}:{port}".format(
            protocol=self.get_http_protocol(),
            login=login,
            host=self.localhost,
            port=self.port,
        )

    def get_public_url(self, login=""):
        """our public url"""
        return "{protocol}://{login}{host}:{port}".format(
            protocol=self.get_http_protocol(),
            login=login,
            host=self.publicip,
            port=self.port,
        )


class ArangodInstance(Instance):
    """represent one arangodb instance"""

    # pylint: disable=too-many-arguments
    def __init__(
        self, typ, port, localhost, publicip, basedir, passvoid, ssl, version, enterprise, is_system=False, jwt=""
    ):
        super().__init__(typ, port, basedir, localhost, publicip, passvoid, "arangod", ssl, version, enterprise, jwt)
        self.is_system = is_system

    def __repr__(self):
        # raise Exception("blarg")
        return """
 {0.name}  |  {0.type_str}  | {0.pid} | {0.logfile}
""".format(
            self
        )

    # pylint: disable=bare-except
    def get_uuid(self):
        """try to load the instances UUID"""
        try:
            uuid_file = self.basedir / "data" / "UUID"
            uuid = uuid_file.read_text()
            return uuid
        except:
            return None

    def get_essentials(self):
        """get the essential attributes of the class"""
        return {
            "name": self.name,
            "pid": self.pid,
            "type": self.type_str,
            "log": self.logfile,
            "is_frontend": self.is_frontend(),
            "url": self.get_public_login_url() if self.is_frontend() else "",
        }

    # pylint: disable=no-else-return
    def get_protocol(self):
        """return protocol of this arangod instance (ssl/tcp)"""
        if self.ssl:
            return "ssl"
        else:
            return "tcp"

    def get_public_login_url(self):
        """our public url with passvoid"""
        return "{protocol}://root:{passvoid}@{publicip}:{port}".format(
            protocol=self.get_http_protocol(),
            passvoid=self.passvoid,
            publicip=self.publicip,
            port=self.port,
        )

    def get_public_plain_url(self):
        """our public url"""
        return "{host}:{port}".format(host=self.publicip, port=self.port)

    def get_endpoint(self):
        """our endpoint"""
        return "{protocol}://{host}:{port}".format(protocol=self.get_protocol(), host=self.localhost, port=self.port)

    def is_frontend(self):
        """is this instance a frontend"""
        # print(repr(self))
        return self.instance_type in [
            InstanceType.COORDINATOR,
            InstanceType.RESILIENT_SINGLE,
            InstanceType.SINGLE,
        ]

    def is_dbserver(self):
        """is this instance a dbserver?"""
        return self.instance_type in [
            InstanceType.DBSERVER,
            InstanceType.RESILIENT_SINGLE,
            InstanceType.SINGLE,
        ]

    def is_sync_instance(self):
        """no."""
        return False

    @step
    def wait_for_logfile(self, tries):
        """wait for logfile to appear"""
        while not self.logfile.exists() and tries:
            progress(":")
            time.sleep(1)
            tries -= 1

    def probe_if_is_leader(self):
        """detect if I am the leader?"""
        return self.get_afo_state() == AfoServerState.LEADER

    @step
    def check_version_request(self, timeout):
        """wait for the instance to reply with 200 to api/version"""
        until = time.time() + timeout
        request_headers = {}
        if self.jwt != "":
            request_headers["Authorization"] = "Bearer " + str(self.jwt)
        while True:
            reply = None
            try:
                reply = {}
                if self.is_frontend():
                    print("fetch frontend version")
                    reply = requests.get(
                        self.get_local_url("") + "/_api/version",
                        auth=HTTPBasicAuth("root", self.passvoid),
                        headers=request_headers,
                        timeout=20,
                    )
                else:
                    print("fetch backend version")
                    reply = requests.get(self.get_local_url("") + "/_api/version", headers=request_headers, timeout=20)
                if reply.status_code == 200:
                    return
                elif reply.status_code == 503 and self.instance_type == InstanceType.RESILIENT_SINGLE:
                    body = reply.json()
                    if "errorNum" in body and body["errorNum"] == 1495:
                        print("Leadership challenge ongoin, prolonging timeout")
                        until += timeout / 10
                print(f'{self.get_local_url("")} got {reply} - {reply.content}')
            except requests.exceptions.ConnectionError:
                print("&")
            if time.time() > until:
                raise TimeoutError("the host would not respond to the version requests on time")
            time.sleep(0.5)

    def get_afo_state(self):
        """is this a leader or follower?"""
        reply = None
        try:
            reply = requests.get(
                self.get_local_url("") + "/_api/version",
                auth=HTTPBasicAuth("root", self.passvoid),
                verify=False,
                timeout=20,
            )
        except requests.exceptions.ConnectionError:
            return AfoServerState.NOT_CONNECTED

        if reply.status_code == 200:
            return AfoServerState.LEADER
        if reply.status_code == 503:
            body_json = json.loads(reply.content)
            # leadership challenge is ongoing...
            if body_json["errorNum"] == 1495:
                return AfoServerState.CHALLENGE_ONGOING
            # leadership challenge is ongoing...
            if body_json["errorNum"] == 1496:
                return AfoServerState.NOT_LEADER
            if body_json["errorNum"] == 503:
                return AfoServerState.STARTUP_MAINTENANCE
            raise Exception("afo_state: unsupported error code in " + str(reply.content))
        raise Exception("afo_state: unsupportet HTTP-Status code " + str(reply.status_code) + str(reply))

    def detect_restore_restart(self):
        """has the server restored their backup restored and is back up"""
        logging.debug("scanning " + str(self.logfile))
        count = 0
        while count < 3000:
            log_file_content = ""
            last_line = ""
            with open(self.logfile, errors="backslashreplace", encoding="utf8") as log_fh:
                for line in log_fh:
                    # skip empty lines
                    if line == "":
                        continue
                    # save last line and append to string
                    # (why not slurp the whole file?)
                    last_line = line
                    log_file_content += "\n" + line

            # check last line or continue
            match = re.search(r"Z \[(\d*)\]", last_line)
            if match is None:
                logging.info("no PID in: %s", last_line)
                continue

            # pid found now find the position of the pid in
            # the logfile and check it is followed by a
            # ready for business.
            pid = match.groups()[0]
            start = log_file_content.find(pid)

            offset = log_file_content.find("RocksDBHotBackupRestore:  restarting server with restored data", start)
            if offset >= 0:
                print("server restarting with restored backup.")
                self.detect_pid(0, offset)
                if self.instance_type == InstanceType.RESILIENT_SINGLE:
                    print("waiting for leader election: ", end="")
                    status = AfoServerState.CHALLENGE_ONGOING
                    while status in [
                        AfoServerState.CHALLENGE_ONGOING,
                        AfoServerState.NOT_CONNECTED,
                        AfoServerState.STARTUP_MAINTENANCE,
                    ]:
                        status = self.get_afo_state()
                        progress("%")
                        time.sleep(0.1)
                    print()
                return
            progress(",")
            time.sleep(0.1)
            count += 1
        raise Exception("timeout waiting for restore restart reached")

    def detect_fatal_errors(self):
        """check whether we have FATAL lines in the logfile"""
        fatal_line = None
        for logfile in [self.logfile] + self.logfiles:
            print(str(logfile))
            with open(logfile, errors="backslashreplace", encoding="utf8") as log_fh:
                for line in log_fh:
                    if fatal_line is not None:
                        fatal_line += "\n" + line
                    elif "] FATAL [" in line:
                        fatal_line = line

        if fatal_line is not None:
            print("Error: ", fatal_line)
            raise Exception("FATAL error found in " + str(self.logfile) + ": " + fatal_line)

    def detect_pid(self, ppid, offset=0, full_binary_path=""):
        """detect the instance"""
        # pylint: disable=too-many-statements disable=too-many-locals disable=too-many-branches
        self.pid = 0
        self.ppid = ppid
        tries = 40
        if IS_MAC:
            tries *= 4
        t_start = ""
        while self.pid == 0 and tries:

            log_file_content = ""
            last_line = ""

            for _ in range(120):
                if self.logfile.exists():
                    break
                time.sleep(1)
            else:
                raise TimeoutError("instance logfile '" + str(self.logfile) + "' didn't show up in 120 seconds")

            with open(self.logfile, errors="backslashreplace", encoding="utf8") as log_fh:
                for line in log_fh:
                    # skip empty lines
                    if line == "":
                        time.sleep(1)
                        continue
                    if "] FATAL [" in line and not self.is_suppressed_log_line(line):
                        print("Error: ", line)
                        raise Exception("FATAL error found in " + str(self.logfile) + ": " + line)
                    # save last line and append to string
                    # (why not slurp the whole file?)
                    last_line = line
                    log_file_content += "\n" + line

            # check last line or continue
            match = re.search(r"Z \[(\d*)\]", last_line)
            if match is None:
                tries -= 1
                logging.info("no PID in [%s]: %s", self.logfile, last_line)
                progress(".")
                time.sleep(1)
                continue

            # pid found now find the position of the pid in
            # the logfile and check it is followed by a
            # ready for business.
            pid = match.groups()[0]
            start = log_file_content.find(pid, offset)
            ready_for_business = "is ready for business."
            pos = log_file_content.find(ready_for_business, start)
            if pos < 0:
                tries -= 1
                progress(".")
                time.sleep(1)
                continue
            self.pid = int(pid)
            # locate the timestamp of our 'ready for business' line:
            match = re.search(
                r"(.*)Z \[" + pid + "].*" + ready_for_business,
                log_file_content[pos - 140 :],
            )
            if match is None:
                tries -= 1
                self.pid = 0
                print("ny" * 40)
                print(log_file_content[pos - 140 :])
                print(log_file_content)
                print(pos)
                time.sleep(1)
                progress(".")
                continue

            t_start = match.group(1)
            logging.debug(
                "found pid {0} for instance with logfile {1} at {2}.".format(self.pid, str(self.logfile), t_start)
            )
            try:
                self.instance = psutil.Process(self.pid)
            except psutil.NoSuchProcess:
                logging.info("process for PID:%d already gone? retrying.", self.pid)
                time.sleep(1)
                self.pid = 0  # a previous log run? retry.
            time.sleep(1)
            progress(":")

        if self.pid == 0:
            print()
            logging.error("could not get pid for instance: " + repr(self))
            logging.error("inspect: " + str(self.logfile))
            raise TimeoutError("could not get pid for instance: " + repr(self))
        logging.info(
            "found process for pid {0} for "
            "instance with logfile {1} at {2}.".format(self.pid, str(self.logfile), t_start)
        )

    def search_for_agent_serving(self):
        """this string is emitted by the agent, if he is leading the agency:
        2021-05-19T16:02:18Z [3447] INFO [a66dc] {agency} AGNT-0dc4dd67-4340-4645-913f-9415adfbeda7
          rebuilt key-value stores - serving.
          this string is emitted when the agent stops leading:
          2023-05-22T02:49:25Z [127808] INFO [f370f] {agency} Set _role to FOLLOWER in term 4
          We search for the latest "serving" string and return its timestamp, if it is not followed
          by the "follower" string
        """
        serving_line = None
        if not self.logfile.exists():
            print(str(self.logfile) + " doesn't exist, skipping.")
            return self.serving
        with open(self.logfile, errors="backslashreplace", encoding="utf8") as log_fh:
            for line in log_fh:
                if "a66dc" in line:
                    serving_line = line
                elif "f370f" in line:
                    serving_line = None
        if serving_line:
            self.serving = log_line_get_date(serving_line)
        return self.serving

    def get_structure(self):
        structure = super().get_structure()
        structure["id"] = self.get_uuid()
        return structure


class ArangodRemoteInstance(ArangodInstance):
    """represent one arangodb instance"""

    # pylint: disable=too-many-arguments
    def __init__(self, typ, port, localhost, publicip, basedir, passvoid, ssl, version, enterprise, jwt=""):
        super().__init__(typ, port, basedir, localhost, publicip, passvoid, "arangod", ssl, version, enterprise, jwt)


class SyncInstance(Instance):
    """represent one arangosync instance"""

    # pylint: disable=too-many-arguments
    def __init__(self, typ, port, localhost, publicip, basedir, passvoid, ssl, version, enterprise, jwt=""):
        super().__init__(typ, port, basedir, localhost, publicip, passvoid, "arangosync", ssl, version, enterprise, jwt)
        self.logfile_parameter = ""
        self.pid_file = None

    def __repr__(self):
        """dump us"""
        # raise Exception("blarg")
        return """
 arangosync instance | type  | pid  | logfile
       {0.name}      | {0.type_str} |  {0.pid} |  {0.logfile}
 """.format(
            self
        )

    def get_essentials(self):
        """get the essential attributes of the class"""
        return {
            "name": self.name,
            "pid": self.pid,
            "type": self.type_str,
            "log": self.logfile,
            "is_frontend": False,
            "url": "",
        }

    def analyze_starter_file_line(self, line):
        if line.find("--log.file") >= 0:
            self.logfile_parameter = line

    # pylint: disable=too-many-branches
    def detect_pid(self, ppid, offset, full_binary_path):
        # first get the starter provided commandline:
        self.ppid = ppid
        self.load_starter_instance_control_file()
        try:
            pidfile = Path(self.instance_arguments[self.instance_arguments.index("--pid-file") + 1])
            if pidfile.exists():
                pid = int(pidfile.read_text(encoding="utf-8"))
                for process in psutil.process_iter():
                    if process.ppid() == ppid and process.pid == pid and process.name() == "arangosync":
                        print(f"identified instance by pid file {pid}")
                        self.pid_file = pidfile
                        self.pid = pid
                        self.instance = psutil.Process(self.pid)
                        return
        except ValueError:
            pass

        logfile_parameter_raw = ""
        try:
            if self.logfile_parameter == "--log.file":
                # newer starters will use '--foo bar' instead of '--foo=bar'
                logfile_parameter_raw = self.instance_arguments[self.instance_arguments.index("--log.file") + 1]
                self.logfile_parameter = "--log.file=" + logfile_parameter_raw
            else:
                logfile_parameter_raw = self.logfile_parameter.split("=")[1]
        except IndexError as ex:
            print(
                f"""{self} - failed to extract the logfile parameter from:
            {self.logfile_parameter} - {self.instance_arguments}"""
            )
            raise ex

        # wait till the process has startet writing its logfile:
        while not self.logfile.exists():
            progress("v")
            time.sleep(1)
        possible_me_pid = []
        count = 0
        while count < 300 and len(possible_me_pid) == 0:
            for process in psutil.process_iter():
                if process.ppid() == ppid and process.name() == "arangosync":
                    proccmd = process.cmdline()[1:]
                    try:
                        # this will throw if its not in there:
                        proccmd.index(self.logfile_parameter)
                        possible_me_pid.append({"p": process.pid, "cmdline": proccmd})
                    except ValueError:
                        try:
                            # this will throw if its not in there:
                            proccmd.index(logfile_parameter_raw)
                            possible_me_pid.append({"p": process.pid, "cmdline": proccmd})
                        except ValueError:
                            pass

            if len(possible_me_pid) == 0 and count > 0:
                progress("s")
                time.sleep(1)
            count += 1

        if len(possible_me_pid) != 1:
            raise Exception("wasn't able to identify my arangosync process! " + str(possible_me_pid))
        self.pid = possible_me_pid[0]["p"]
        self.instance = psutil.Process(self.pid)

    def wait_for_logfile(self, tries):
        """not implemented"""

    def is_frontend(self):
        """no."""
        return False

    def is_dbserver(self):
        """no."""
        return False

    def is_sync_instance(self):
        """yes."""
        return True

    def is_line_relevant(self, line):
        """it returns true if the line from logs should be printed"""
        # return False# TODO: GT-472
        # if "|FATAL|" in line or "|ERRO|" in line or "|WARN|" in line:
        #    # logs from arangosync v1
        #    return True
        # if " FTL " in line or " ERR " in line or " WRN " in line or 'panic:' in line:
        #    # logs from arangosync v2
        #    return True
        #
        # return False

    def is_line_fatal(self, line):
        """it returns true if the line from logs should be printed"""
        return False  # TODO: GT-472
        # if "|FATAL|" in line:
        #    # logs from arangosync v1
        #    return True
        # if " FTL " in line or 'panic:' in line:
        #    # logs from arangosync v2
        #    return True
        #
        # return False

    def get_public_plain_url(self):
        """get the public connect URL"""
        return "{host}:{port}".format(host=self.publicip, port=self.port)


def get_instances_table(instances):
    """print all instances provided in tabular format"""
    table = BeautifulTable(maxwidth=160)
    for one_instance in instances:
        table.rows.append(
            [
                one_instance["name"],
                one_instance["pid"],
                one_instance["type"],
                one_instance["log"],
                # one_instance["is_frontend"],
                one_instance["url"],
            ]
        )
    table.columns.header = [
        "Name",
        "PID",
        "type",
        "Logfile",
        # "Frontend",
        "URL",
    ]
    return table


def print_instances_table(instances):
    """print all instances provided in tabular format"""
    table = get_instances_table(instances)
    print(str(table))
    attach_table(table, "Instances table")
