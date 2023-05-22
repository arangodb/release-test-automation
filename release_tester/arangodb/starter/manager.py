#!/usr/bin/env python
""" Manage one instance of the arangodb starter
    to crontroll multiple arangods
"""

import copy
import datetime
import http.client as http_client
import logging
import os
import re
import subprocess
import sys
import time

from pathlib import Path
import psutil
import requests
import semver
from allure_commons._allure import attach
from allure_commons.types import AttachmentType

from arangodb.instance import (
    ArangodInstance,
    ArangodRemoteInstance,
    SyncInstance,
    InstanceType,
    AfoServerState,
    get_instances_table,
)
from arangodb.backup import HotBackupConfig, HotBackupManager
from arangodb.sh import ArangoshExecutor
from arangodb.imp import ArangoImportExecutor
from arangodb.restore import ArangoRestoreExecutor
from arangodb.bench import ArangoBenchManager

from tools.asciiprint import print_progress as progress
from tools.timestamp import timestamp
import tools.loghelper as lh
from tools.killall import get_process_tree
from tools.utils import is_column_cache_supported, COLUMN_CACHE_ARGUMENT

from reporting.reporting_utils import attach_table, step, attach_http_request_to_report, attach_http_response_to_report

IS_WINDOWS = sys.platform == "win32"

# pylint: disable=too-many-lines
class StarterManager:
    """manages one starter instance"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=dangerous-default-value disable=too-many-statements disable=too-many-public-methods disable=method-hidden disable=too-many-branches
    def __init__(
        self,
        basecfg,
        install_prefix,
        instance_prefix,
        expect_instances,
        mode=None,
        port=None,
        jwt_str=None,
        moreopts=[],
    ):
        self.expect_instances = expect_instances
        self.expect_instances.sort()
        self.cfg = copy.deepcopy(basecfg)
        self.moreopts = self.cfg.default_starter_args + moreopts
        if self.cfg.verbose:
            self.moreopts += ["--log.verbose=true"]
            # self.moreopts += ['--all.log', 'startup=debug']
        # self.moreopts += ["--args.coordinators.query.memory-limit=123456" ]
        # self.moreopts += ["--all.query.memory-limit=123456" ]
        # self.moreopts += ["--all.log.level=arangosearch=trace"]
        # self.moreopts += ["--all.log.level=startup=trace"]
        # self.moreopts += ["--all.log.level=engines=trace"]
        # self.moreopts += ["--all.log.escape-control-chars=true"]
        # self.moreopts += ["--all.log.escape-unicode-chars=true"]
        # Split logmessages of facilities into several logfiles to reduce load on the main log:
        # self.moreopts += ["--all.log.output=general=file://@ARANGODB_SERVER_DIR@/arangod.log"]
        # self.moreopts += ["--all.log.output=startup=file://@ARANGODB_SERVER_DIR@/arangod_startup.log"]
        # self.moreopts += ["--starter.disable-ipv6=false"]
        # self.moreopts += ["--starter.host=127.0.0.1"]

        self.moreopts += [
            "--all.rclone.argument=--log-level=DEBUG",
            "--all.rclone.argument=--log-file=@ARANGODB_SERVER_DIR@/rclone.log",
        ]
        if (self.cfg.semver.major == 3 and self.cfg.semver.minor >= 9) or (self.cfg.semver.major > 3):
            self.moreopts += ["--args.all.database.extended-names-databases=true"]
        print(self.moreopts)
        # directories
        self.raw_basedir = install_prefix
        self.old_install_prefix = self.cfg.install_prefix
        self.name = str(install_prefix / instance_prefix)  # this is magic with the name function.
        self.basedir = self.cfg.base_test_dir / install_prefix / instance_prefix
        self.basedir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.basedir / "arangodb.log"

        # arg port - can be set - otherwise it is read from the log later
        self.starter_port = port
        if self.starter_port is not None:
            self.moreopts += ["--starter.port", "%d" % self.starter_port]

        self.hotbackup_args = []
        if self.cfg.hot_backup_supported:
            self.moreopts += ["--all.log.level=backup=trace"]
            self.hotbackup_args = [
                "--all.rclone.executable",
                self.cfg.real_sbin_dir / "rclone-arangodb",
            ]

        if self.cfg.encryption_at_rest:
            self.keyfile = self.basedir / "key.txt"
            # generate pseudo random key of length 32:
            self.keyfile.write_text((str(datetime.datetime.now()) * 5)[0:32])
            self.moreopts += ["--rocksdb.encryption-keyfile", str(self.keyfile)]
        self.hb_instance = None
        self.hb_config = None
        # arg - jwtstr
        self.jwtfile = None
        self.jwt_header = None
        self.jwt_tokens = {}
        if jwt_str:
            self.jwtfile = Path(str(self.basedir) + "_jwt")
            self.jwtfile.write_text(jwt_str, encoding="utf-8")
            self.moreopts += ["--auth.jwt-secret", str(self.jwtfile)]
            self.get_jwt_header()

        self.passvoidfile = Path(str(self.basedir) + "_passvoid")

        if self.cfg.ssl and self.cfg.use_auto_certs:
            self.moreopts += ["--ssl.auto-key"]

        # arg mode
        self.mode = mode
        if self.mode:
            self.moreopts += ["--starter.mode", self.mode]
            if self.mode == "single":
                self.expect_instance_count = 1  # Only single server
            elif self.mode == "activefailover":
                self.expect_instance_count = 2  # agent + server
            elif self.mode == "cluster":
                self.expect_instance_count = 3  # agent + dbserver + coordinator
                if "--starter.local" in moreopts:
                    # full cluster on this starter:
                    self.expect_instance_count *= 3
                if "--starter.sync" in moreopts:
                    self.expect_instance_count += 2  # syncmaster + syncworker

        self.username = "root"
        self.passvoid = ""

        self.instance = None  # starter instance - PsUtil Popen child
        self.frontend_port = None  # required for swith in active failover setup
        self.all_instances = []  # list of starters arangod child instances

        self.is_master = None
        self.is_leader = False
        self.arangosh = None
        self.arango_importer = None
        self.arango_restore = None
        self.arangobench = None
        self.executor = None  # meaning?
        self.sync_master_port = None
        self.coordinator = None  # meaning - port
        self.expect_instance_count = 1
        self.startupwait = 2
        self.supports_foxx_tests = True

        self.upgradeprocess = None

        self.arguments = [
            "--log.console=false",
            "--log.file=true",
            "--starter.data-dir={0.basedir}".format(self),
        ] + self.moreopts
        self.old_version = self.cfg.version
        self.enterprise = self.cfg.enterprise

    def __repr__(self):
        return str(get_instances_table(self.get_instance_essentials()))

    def get_structure(self):
        """serialize the instance info compatible with testing.js"""
        instances = []
        urls = []
        leader_name = ""
        if self.is_leader:
            leader_name = self.name

        for arangod in self.all_instances:
            struct = arangod.get_structure()
            struct["JWT_header"] = self.get_jwt_header()
            urls.append(struct["url"])
            instances.append(struct)
        return {
            "protocol": self.get_http_protocol(),
            "options": "",
            "addArgs": "",
            "rootDir": str(self.basedir),
            "leader": leader_name,
            "agencyConfig": "",
            "httpAuthOptions": "",
            "urls": str(urls),
            "arangods": instances,
            "JWT_header": self.get_jwt_header(),
            # 'url': self.url,
            # 'endpoints': self.endpoints,
            # 'endpoint': self.endpoint,
            # 'restKeyFile': self.restKeyFile,
            # 'tcpdump': self.tcpdump,
            # 'cleanup': self.cleanup
        }

    def name(self):
        """name of this starter"""
        return str(self.name)

    def get_frontends(self):
        """get the frontend URLs of this starter instance"""
        ret = []
        for i in self.all_instances:
            if i.is_frontend():
                ret.append(i)
        return ret

    def get_dbservers(self):
        """get the list of dbservers managed by this starter"""
        ret = []
        for i in self.all_instances:
            if i.is_dbserver():
                ret.append(i)
        return ret

    def get_agents(self):
        """get the list of agents managed by this starter"""
        ret = []
        for i in self.all_instances:
            if i.instance_type == InstanceType.AGENT:
                ret.append(i)
        return ret

    def get_sync_masters(self):
        """get the list of arangosync masters managed by this starter"""
        ret = []
        for i in self.all_instances:
            if i.instance_type == InstanceType.SYNCMASTER:
                ret.append(i)
        return ret

    def get_frontend(self):
        """get the first frontendhost of this starter"""
        servers = self.get_frontends()
        assert servers, "starter: don't have instances!"
        return servers[0]

    def get_dbserver(self):
        """get the first dbserver of this starter"""
        servers = self.get_dbservers()
        assert servers, "starter: don't have instances!"
        return servers[0]

    def get_agent(self):
        """get the first agent of this starter"""
        servers = self.get_agents()
        assert servers, "starter: have no instances!"
        return servers[0]

    def get_sync_master(self):
        """get the first arangosync master of this starter"""
        servers = self.get_sync_masters()
        assert servers, "starter: don't have instances!"
        return servers[0]

    def have_this_instance(self, instance):
        """detect whether this manager manages instance"""
        for i in self.all_instances:
            if i == instance:
                print("YES ITS ME!")
                return True
        print("NO S.B. ELSE")
        return False

    def get_instance_essentials(self):
        """get the essentials of all instances controlled by this starter"""
        ret = []
        for instance in self.all_instances:
            ret.append(instance.get_essentials())
        return ret

    def show_all_instances(self):
        """print all instances of this starter to the user"""
        if not self.all_instances:
            logging.error("%s: no instances detected", self.name)
            return
        instances = ""
        for instance in self.all_instances:
            instances += " - {0.name} (pid: {0.pid})".format(instance)
        logging.info("arangod instances for starter: %s - %s", self.name, instances)

    @step
    def run_starter(self, expect_to_fail=False):
        """launch the starter for this instance"""
        logging.info("running starter " + self.name)
        args = [self.cfg.bin_dir / "arangodb"] + self.hotbackup_args + self.arguments

        assert self.cfg.version
        # Remove it if it is not needed
        if not is_column_cache_supported(self.cfg.version) or not self.cfg.enterprise:
            if COLUMN_CACHE_ARGUMENT in args:
                args.remove(COLUMN_CACHE_ARGUMENT)

        # Add it if it is required
        if is_column_cache_supported(self.cfg.version) and self.cfg.enterprise:
            if COLUMN_CACHE_ARGUMENT not in args:
                args.append(COLUMN_CACHE_ARGUMENT)

        lh.log_cmd(args)
        self.instance = psutil.Popen(args)
        logging.info("my starter has PID:" + str(self.instance.pid))
        if not expect_to_fail:
            self.wait_for_logfile()
            self.wait_for_port_bind()

    @step
    def attach_running_starter(self):
        """somebody else is running the party, but we also want to have a look"""
        # pylint disable=broad-except
        match_str = "--starter.data-dir={0.basedir}".format(self)
        if self.passvoidfile.exists():
            self.passvoid = self.passvoidfile.read_text(errors="backslashreplace", encoding="utf-8")
        for process in psutil.process_iter(["pid", "name"]):
            try:
                name = process.name()
                if name.startswith("arangodb"):
                    process = psutil.Process(process.pid)
                    if any(match_str in s for s in process.cmdline()):
                        print(process.cmdline())
                        print("attaching " + str(process.pid))
                        self.instance = process
                        return
            except psutil.NoSuchProcess as ex:
                logging.error(ex)
        raise Exception("didn't find a starter for " + match_str)

    def set_jwt_file(self, filename):
        """some scenarios don't want to use the builtin jwt generation from the manager"""
        self.jwtfile = filename

    def get_jwt_token_from_secret_file(self, filename):
        """retrieve token from the JWT secret file which is cached for the future use"""
        # pylint: disable=consider-iterating-dictionary
        if filename in self.jwt_tokens.keys():
            # token for that file was checked already.
            return self.jwt_tokens[filename]

        cmd = [
            self.cfg.bin_dir / "arangodb",
            "auth",
            "header",
            "--auth.jwt-secret",
            str(filename),
        ]
        print(cmd)
        jwt_proc = psutil.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info("JWT starter has PID:" + str(jwt_proc.pid))

        (header, err) = jwt_proc.communicate()
        jwt_proc.wait()
        if len(str(err)) > 3:
            raise Exception("error invoking the starter " "to generate the jwt header token! " + str(err))
        if len(str(header).split(" ")) != 3:
            raise Exception("failed to parse the output" " of the header command: " + str(header))

        self.jwt_tokens[filename] = str(header).split(" ")[2].split("\\")[0]
        return self.jwt_tokens[filename]

    def get_jwt_header(self):
        """return jwt header from current installation"""
        if self.jwt_header:
            return self.jwt_header
        self.jwt_header = self.get_jwt_token_from_secret_file(str(self.jwtfile))
        return self.jwt_header

    @step
    def set_passvoid(self, passvoid, write_to_server=True):
        """set the passvoid to the managed instance"""
        if write_to_server:
            print("Provisioning passvoid " + passvoid)
            self.arangosh.js_set_passvoid("root", passvoid)
            self.passvoidfile.write_text(passvoid, encoding="utf-8")
        self.passvoid = passvoid
        for i in self.all_instances:
            if i.is_frontend():
                i.set_passvoid(passvoid)
        self.cfg.passvoid = passvoid

    def get_passvoid(self):
        """get the passvoid to the managed instance"""
        return self.passvoid

    @step
    def send_request(self, instance_type, verb_method, url, data=None, headers={}, timeout=None):
        """send an http request to the instance"""
        http_client.HTTPConnection.debuglevel = 1

        results = []
        for instance in self.all_instances:
            if instance.instance_type == instance_type:
                if instance.detect_gone():
                    print("Instance to send request to already gone: " + repr(instance))
                else:
                    headers["Authorization"] = "Bearer " + str(self.get_jwt_header())
                    base_url = instance.get_public_plain_url()
                    full_url = self.get_http_protocol() + "://" + base_url + url
                    attach_http_request_to_report(verb_method.__name__, full_url, headers, data)
                    reply = verb_method(
                        full_url,
                        data=data,
                        headers=headers,
                        allow_redirects=False,
                        timeout=timeout,
                        verify=False,
                    )
                    attach_http_response_to_report(reply)
                    results.append(reply)
        http_client.HTTPConnection.debuglevel = 0
        return results

    @step
    def crash_instances(self):
        """make all managed instances plus the starter itself crash."""
        try:
            if self.instance.status() == psutil.STATUS_RUNNING or self.instance.status() == psutil.STATUS_SLEEPING:
                print("generating coredump for " + str(self.instance))
                gcore = psutil.Popen(["gcore", str(self.instance.pid)], cwd=self.basedir)
                print("launched GCORE with PID:" + str(gcore.pid))
                gcore.wait()
                self.kill_instance()
            else:
                print("NOT generating coredump for " + str(self.instance))
        except psutil.NoSuchProcess:
            logging.info("instance already dead: " + str(self.instance))

        for instance in self.all_instances:
            instance.crash_instance()

    def is_instance_running(self):
        """check whether this is still running"""
        try:
            self.instance.wait(timeout=1)
        except psutil.TimeoutExpired:
            pass
        return self.instance.is_running()

    @step
    def wait_for_logfile(self):
        """wait for our instance to create a logfile"""
        counter = 0
        keep_going = True
        logging.info("Looking for log file.\n")
        while keep_going:
            self.check_that_instance_is_alive()
            if counter == 20:
                raise Exception("logfile did not appear: " + str(self.log_file))
            counter += 1
            logging.info("counter = " + str(counter))
            if self.log_file.exists():
                logging.info("Found: " + str(self.log_file) + "\n")
                keep_going = False
            time.sleep(1)

    @step
    def wait_for_port_bind(self):
        """wait for our instance to bind its TCP-ports"""
        if self.starter_port is not None:
            count = 0
            while count < 10:
                for socket in self.instance.connections():
                    if socket.status == "LISTEN" and socket.laddr.port == self.starter_port:
                        print("socket found!")
                        return
                count += 1
                time.sleep(1)
            raise Exception(f"starter didn't bind {self.starter_port} on time!")
        print("dont know port")

    @step
    def wait_for_upgrade_done_in_log(self, timeout=120):
        """in single server mode the 'upgrade' commander exits before
        the actual upgrade is finished. Hence we need to look into
        the logfile of the managing starter if it thinks its finished.
        """
        keep_going = True
        logging.info('Looking for "Upgrading done" in the log file.\n')
        while keep_going:
            text = self.get_log_file()
            pos = text.find("Upgrading done.")
            keep_going = pos == -1
            if keep_going:
                time.sleep(1)
            progress(".")
            timeout -= 1
            if timeout <= 0:
                raise TimeoutError("upgrade of leader follower not found on time")
        for instance in self.all_instances:
            instance.wait_for_shutdown()

    @step
    def is_instance_up(self):
        """check whether all spawned arangods are fully bootet"""
        logging.debug("checking if starter instance booted: " + str(self.basedir))
        if not self.instance.is_running():
            message = "Starter Instance {0.name} is gone!".format(self)
            logging.error(message)
            raise Exception(message)

        # if the logfile contains up and running we are fine
        lfs = self.get_log_file()
        regx = re.compile(r"(\w*) up and running ")
        for line in lfs.splitlines():
            match = regx.search(line)
            if match:
                groups = match.groups()
                if len(groups) == 1 and groups[0] == "agent":
                    continue
                return True

        return False

    @step
    def terminate_instance(self, keep_instances=False):
        """terminate the instance of this starter
        (it should kill all its managed services)"""

        lh.subsubsection("terminating instances for: " + str(self.name))
        logging.info("StarterManager: Terminating starter instance: %s", str(self.arguments))

        logging.info("This should terminate all child processes")
        self.instance.terminate()
        logging.info("StarterManager: waiting for process to exit")
        exit_code = self.instance.wait()
        self.add_logfile_to_report()
        # workaround BTS-815: starter exits 15 on the wintendo:
        if IS_WINDOWS and exit_code == 15:
            exit_code = 0

        if exit_code != 0:
            raise Exception("Starter %s exited with %d" % (self.basedir, exit_code))

        old_log = self.basedir / "arangodb.log.old"
        logging.info(
            "StarterManager: done - moving logfile from %s to %s",
            str(self.log_file),
            str(old_log),
        )
        if old_log.exists():
            old_log.unlink()
        self.log_file.rename(old_log)

        for instance in self.all_instances:
            instance.rename_logfile()
            if not instance.detect_gone():
                print("Manually terminating instance!")
                instance.terminate_instance(False)

        if keep_instances:
            for i in self.all_instances:
                i.pid = None
                i.ppid = None
        else:
            # Clear instances as they have been stopped and the logfiles
            # have been moved.
            self.is_leader = False
            self.all_instances = []

    @step
    def kill_instance(self):
        """kill the instance of this starter
        (it won't kill its managed services)"""
        logging.info("StarterManager: Killing: %s", str(self.arguments))
        self.instance.kill()
        try:
            logging.info(str(self.instance.wait(timeout=45)))
            self.add_logfile_to_report()
        except Exception as ex:
            raise Exception("Failed to KILL the starter instance? " + repr(self)) from ex

        logging.info("StarterManager: Instance now dead.")
        self.instance = None

    def replace_binary_for_upgrade(self, new_install_cfg, relaunch=True):
        """
        - replace the parts of the installation with information
          after an upgrade
        - kill the starter processes of the old version
        - revalidate that the old arangods are still running and alive
        - replace the starter binary with a new one.
          this has not yet spawned any children
        """
        # On windows the install prefix may change,
        # since we can't overwrite open files:
        self.enterprise = new_install_cfg.enterprise
        self.replace_binary_setup_for_upgrade(new_install_cfg)
        with step("kill the starter processes of the old version"):
            logging.info("StarterManager: Killing my instance [%s]", str(self.instance.pid))
            self.kill_instance()
        with step("revalidate that the old arangods are still running and alive"):
            self.detect_instance_pids_still_alive()
        if relaunch:
            with step("replace the starter binary with a new one," + " this has not yet spawned any children"):
                self.respawn_instance(new_install_cfg.version)
                logging.info("StarterManager: respawned instance as [%s]", str(self.instance.pid))

    @step
    def kill_specific_instance(self, which_instances):
        """kill specific instances of this starter
        (it won't kill starter itself)"""
        for instance_type in which_instances:
            for instance in self.all_instances:
                if instance.instance_type == instance_type:
                    instance.terminate_instance()

    @step
    def manually_launch_instances(self, which_instances, moreargs, waitpid=True, kill_instance=False):
        """launch the instances of this starter with optional arguments"""
        for instance_type in which_instances:
            for instance in self.all_instances:
                if instance.instance_type == instance_type:
                    if kill_instance:
                        instance.kill_instance()
                    instance.launch_manual_from_instance_control_file(
                        self.cfg.sbin_dir,
                        self.old_install_prefix,
                        self.cfg.install_prefix,
                        self.cfg.version,
                        self.enterprise,
                        moreargs,
                        waitpid,
                    )

    @step
    def manually_launch_instances_for_upgrade(self, which_instances, moreargs, waitpid=True, kill_instance=False):
        """launch the instances of this starter with optional arguments"""
        for instance_type in which_instances:
            for i in self.all_instances:
                if i.instance_type == instance_type:
                    if kill_instance:
                        i.kill_instance()
                    i.launch_manual_from_instance_control_file(
                        self.cfg.sbin_dir,
                        self.old_install_prefix,
                        self.cfg.install_prefix,
                        self.cfg.version,
                        self.enterprise,
                        moreargs,
                        waitpid,
                    )

    # pylint: disable=unused-argument
    @step
    def upgrade_instances(self, which_instances, moreargs, waitpid=True, force_kill_fatal=True):
        """kill, launch the instances of this starter with optional arguments and restart"""
        for instance_type in which_instances:
            for i in self.all_instances:
                if i.instance_type == instance_type:
                    i.terminate_instance()
                    i.launch_manual_from_instance_control_file(
                        self.cfg.sbin_dir,
                        self.old_install_prefix,
                        self.cfg.install_prefix,
                        self.cfg.version,
                        self.enterprise,
                        moreargs,
                        True,
                    )
                    i.launch_manual_from_instance_control_file(
                        self.cfg.sbin_dir,
                        self.old_install_prefix,
                        self.cfg.install_prefix,
                        self.cfg.version,
                        self.enterprise,
                        [],
                        False,
                    )

    @step
    def restart_arangods(self):
        """Terminate arangod(s). Let the starter restart them."""
        for instance in self.all_instances:
            instance.kill_instance()
            instance.rename_logfile()
        self.detect_instances()

    @step
    def replace_binary_setup_for_upgrade(self, new_install_cfg):
        """replace the parts of the installation with information after an upgrade"""
        # On windows the install prefix may change,
        # since we can't overwrite open files:
        self.cfg.set_directories(new_install_cfg)
        if self.cfg.hot_backup_supported:
            self.hotbackup_args = [
                "--all.rclone.executable",
                self.cfg.real_sbin_dir / "rclone-arangodb",
            ]

    @step
    def kill_sync_processes(self, force, rev):
        """kill all arangosync instances we posses"""
        for i in self.all_instances:
            if i.is_sync_instance():
                if not force and i.pid_file is not None and rev >= semver.VersionInfo.parse("0.15.0"):
                    print("Skipping manual kill")
                    return
                logging.info("manually killing syncer: " + str(i.pid))
                i.terminate_instance()

    @step
    def command_upgrade(self):
        """
        we use a starter, to tell daemon starters to perform the rolling upgrade
        """
        args = [
            self.cfg.bin_dir / "arangodb",
            "upgrade",
            "--starter.endpoint",
            self.get_http_protocol() + "://127.0.0.1:" + str(self.get_my_port()),
        ]
        logging.info("StarterManager: Commanding upgrade %s", str(args))
        self.upgradeprocess = psutil.Popen(
            args,
            # stdout=subprocess.PIPE,
            # stdin=subprocess.PIPE,
            # stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        print("Upgrade commander has PID:" + str(self.upgradeprocess.pid))

    @step
    def wait_for_upgrade(self, timeout=60):
        """wait for the upgrade commanding starter to finish"""
        ret = None
        try:
            ret = self.upgradeprocess.wait(timeout=timeout)
        except psutil.TimeoutExpired as timeout_ex:
            msg = "StarterManager: Upgrade command [%s] didn't finish in time: %d" % (
                str(self.basedir),
                timeout,
            )
            raise TimeoutError(msg) from timeout_ex
        logging.info(
            "StarterManager: Upgrade command [%s] exited: %s",
            str(self.basedir),
            str(ret),
        )
        if ret != 0:
            raise Exception("Upgrade process exited with non-zero reply")

    @step
    def wait_for_restore(self):
        """
        tries to wait for the server to restart after the 'restore' command
        """
        for node in self.all_instances:
            if node.instance_type in [
                InstanceType.RESILIENT_SINGLE,
                InstanceType.SINGLE,
                InstanceType.DBSERVER,
            ]:
                node.detect_restore_restart()

    @step
    def tcp_ping_nodes(self):
        """
        tries to wait for the server to restart after the 'restore' command
        """
        for node in self.all_instances:
            if node.instance_type in [
                InstanceType.RESILIENT_SINGLE,
                InstanceType.SINGLE,
                InstanceType.DBSERVER,
            ]:
                node.check_version_request(20.0)

    @step
    def respawn_instance(self, version, moreargs=[], wait_for_logfile=True):
        """
        restart the starter instance after we killed it eventually,
        maybe command manual upgrade (and wait for exit)
        """
        args = [self.cfg.bin_dir / "arangodb"] + self.hotbackup_args + self.arguments + moreargs

        assert version is not None
        # Remove it if it is not needed
        if not is_column_cache_supported(version) or not self.cfg.enterprise:
            if COLUMN_CACHE_ARGUMENT in args:
                args.remove(COLUMN_CACHE_ARGUMENT)

        # Add it if it is required
        if is_column_cache_supported(version) and self.cfg.enterprise:
            if COLUMN_CACHE_ARGUMENT not in args:
                args.append(COLUMN_CACHE_ARGUMENT)

        logging.info("StarterManager: respawning instance %s", str(args))
        self.instance = psutil.Popen(args)
        self.pid = self.instance.pid
        self.ppid = self.instance.ppid()
        print("respawned with PID:" + str(self.instance.pid))
        if wait_for_logfile:
            self.wait_for_logfile()
            self.wait_for_port_bind()
        else:
            print("Waiting for starter to exit")
            print("Starter exited %d" % self.instance.wait())

    @step
    def wait_for_version_reply(self):
        """wait for the SUT reply with a 200 to /_api/version"""
        frontends = self.get_frontends()
        for frontend in frontends:
            # we abuse this function:
            while frontend.get_afo_state() != AfoServerState.LEADER:
                progress(".")
                time.sleep(0.1)

    @step
    def execute_frontend(self, cmd, verbose=True):
        """use arangosh to run a command on the frontend arangod"""
        return self.arangosh.run_command(cmd, verbose)

    def get_frontend_port(self):
        """get the port of the arangod which is coordinator etc."""
        if self.frontend_port:
            return self.frontend_port
        return self.get_frontend().port

    def get_my_port(self):
        """find out my frontend port"""
        if self.starter_port is not None:
            return self.starter_port

        where = -1
        tries = 10
        while where == -1 and tries:
            tries -= 1
            lfcontent = self.get_log_file()
            where = lfcontent.find("ArangoDB Starter listening on")
            if where != -1:
                where = lfcontent.find(":", where)
                if where != -1:
                    end = lfcontent.find(" ", where)
                    port = lfcontent[where + 1 : end]
                    self.starter_port = port
                    assert int(port), "port cannot be converted to int!"
                    return port
            logging.info("retrying logfile")
            time.sleep(1)
        message = "could not get port form: " + self.log_file
        logging.error(message)
        raise Exception(message)

    def get_sync_master_port(self):
        """get the port of a syncmaster arangosync"""
        self.sync_master_port = None
        pos = None
        sm_port_text = "Starting syncmaster on port"
        sw_text = "syncworker up and running"
        worker_count = 0
        logging.info("detecting sync master port")
        while worker_count < 3 and self.is_instance_running():
            progress("%")
            lfs = self.get_log_file()
            npos = lfs.find(sw_text, pos)
            if npos >= 0:
                worker_count += 1
                pos = npos + len(sw_text)
            else:
                time.sleep(1)
        lfs = self.get_log_file()
        pos = lfs.find(sm_port_text)
        pos = lfs.find(sm_port_text, pos + len(sm_port_text))
        pos = lfs.find(sm_port_text, pos + len(sm_port_text))
        if pos >= 0:
            pos = pos + len(sm_port_text) + 1
            self.sync_master_port = int(lfs[pos : pos + 4])
        return self.sync_master_port

    @step
    def get_log_file(self):
        """fetch the logfile of this starter"""
        return self.log_file.read_text(errors="backslashreplace")

    def read_db_logfile(self):
        """get the logfile of the dbserver instance"""
        server = self.get_dbserver()
        assert server.logfile.exists(), "don't have logfile?"
        return server.logfile.read_text(errors="backslashreplace")

    @step
    def read_agent_logfile(self):
        """get the agent logfile of this instance"""
        server = self.get_agent()
        assert server.logfile.exists(), "don't have logfile?"
        return server.logfile.read_text(errors="backslashreplace")

    @step
    def detect_instances(self):
        """see which arangods where spawned and inspect their logfiles"""
        lh.subsection("Instance Detection for {0.name}".format(self))
        self.all_instances = []
        logging.debug("waiting for frontend")
        logfiles = set()  # logfiles that can be used for debugging

        # the more instances we expect to spawn the more patient:
        tries = 10 * self.expect_instance_count

        # Wait for forntend to become alive.
        all_instances_up = False
        while not all_instances_up and tries:
            self.all_instances = []
            detected_instances = []
            sys.stdout.write(".")
            sys.stdout.flush()

            for root, dirs, files in os.walk(self.basedir):
                for onefile in files:
                    # logging.debug("f: " + root + os.path.sep + onefile)
                    if onefile.endswith("log"):
                        logfiles.add(str(Path(root) / onefile))

                for name in dirs:
                    # logging.debug("d: " + root + os.path.sep + name)
                    match = None
                    instance_class = None
                    if name.startswith("sync"):
                        match = re.match(r"(syncmaster|syncworker)(\d*)", name)
                        instance_class = SyncInstance
                    else:
                        match = re.match(
                            r"(agent|coordinator|dbserver|resilientsingle|single)(\d*)",
                            name,
                        )
                        instance_class = ArangodInstance
                    # directory = self.basedir / name
                    if match and len(match.group(2)) > 0:
                        # we may see a `local-slave-*` directory inbetween,
                        # hence we need to choose the current directory not
                        # the starter toplevel dir for this:
                        instance = instance_class(
                            match.group(1),
                            match.group(2),
                            self.cfg.localhost,
                            self.cfg.publicip,
                            Path(root) / name,
                            self.passvoid,
                            self.cfg.ssl,
                            self.cfg.version,
                            self.enterprise,
                        )
                        instance.wait_for_logfile(tries)
                        instance.detect_pid(
                            ppid=self.instance.pid,
                            full_binary_path=self.cfg.real_sbin_dir,
                            offset=0,
                        )
                        detected_instances.append(instance.instance_type)
                        self.all_instances.append(instance)

            print(self.expect_instances)
            detected_instances.sort()
            print(detected_instances)
            attach(str(self.expect_instances), "Expected instances")
            attach(str(detected_instances), "Detected instances")
            if (self.expect_instances != detected_instances) or (not self.get_frontends()):
                tries -= 1
                time.sleep(5)
            else:
                all_instances_up = True

        if not self.get_frontends():
            print()
            logging.error("STARTER FAILED TO SPAWN ARANGOD")
            self.show_all_instances()
            logging.error("can not continue without frontend instance")
            logging.error("please check logs in" + str(self.basedir))
            for logf in logfiles:
                logging.debug(logf)
            message = "if that does not help try to delete: " + str(self.basedir)
            logging.error(message)
            raise Exception(message)
        self.show_all_instances()

    @step
    def detect_instance_pids(self):
        """detect the arangod instance PIDs"""
        for instance in self.all_instances:
            instance.detect_pid(
                ppid=self.instance.pid,
                full_binary_path=self.cfg.real_sbin_dir,
                offset=0,
            )

        self.show_all_instances()
        self.detect_arangosh_instances()

    @step
    def detect_fatal_errors(self):
        """scan all instances for `FATAL` statements"""
        for instance in self.all_instances:
            instance.detect_fatal_errors()

    @step
    def detect_arangosh_instances(self):
        """
        gets the arangosh instance to speak to the frontend of this starter
        """
        if self.arangosh is None:
            self.cfg.port = self.get_frontend_port()

            self.arangosh = ArangoshExecutor(self.cfg, self.get_frontend())
            self.arango_importer = ArangoImportExecutor(self.cfg, self.get_frontend())
            self.arango_restore = ArangoRestoreExecutor(self.cfg, self.get_frontend())
            if self.cfg.hot_backup_supported:
                self.cfg.passvoid = self.passvoid
                self.hb_instance = HotBackupManager(
                    self.cfg,
                    self.raw_basedir,
                    self.cfg.base_test_dir / self.raw_basedir,
                    self.get_frontend(),
                )
                self.hb_config = HotBackupConfig(
                    self.cfg,
                    self.raw_basedir,
                    self.cfg.base_test_dir / self.raw_basedir,
                )

    @step
    def launch_arangobench(self, testacse_no, moreopts=[]):
        """launch an arangobench instance to the frontend of this starter"""
        arangobench = ArangoBenchManager(self.cfg, self.get_frontend())
        arangobench.launch(testacse_no, moreopts)
        return arangobench

    @step
    def detect_instance_pids_still_alive(self):
        """
        detecting whether the processes the starter spawned are still there
        """
        missing_instances = []
        running_pids = psutil.pids()
        for instance in self.all_instances:
            if instance.pid not in running_pids:
                missing_instances.append(instance)

        if len(missing_instances) > 0:
            logging.error(
                "Not all instances are alive. " "The following are not running: %s",
                str(missing_instances),
            )
            logging.error(get_process_tree())
            raise Exception("instances missing: " + str(missing_instances))
        instances_table = get_instances_table(self.get_instance_essentials())
        logging.info("All arangod instances still running: \n%s", str(instances_table))
        attach_table(instances_table, "Instances table")

    @step
    def maintainance(self, on_off, instance_type):
        """enables / disables maintainance mode"""
        print(("enabling" if on_off else "disabling") + " Maintainer mode")
        tries = 60
        while True:
            reply = self.send_request(
                instance_type,
                requests.put,
                "/_admin/cluster/maintenance",
                '"on"' if on_off else '"off"',
            )
            if len(reply) > 0:
                print("Reply: " + str(reply[0].text))
                if reply[0].status_code == 200:
                    return
                print(f"Reply status code is {reply[0].status_code}. Sleeping for 3 s.")
                time.sleep(3)
                tries -= 1
            else:
                print("Reply is empty. Sleeping for 3 s.")
                time.sleep(3)
                tries -= 1
            if tries <= 0:
                action = "enable" if on_off else "disable"
                raise Exception(f"Couldn't {action} maintainance mode!")

    @step
    def detect_leader(self):
        """in active failover detect whether we run the leader"""
        # Should this be moved to the AF script?
        lfs = self.read_db_logfile()

        became_leader = lfs.find("Became leader in") >= 0
        took_over = lfs.find("Successful leadership takeover:" + " All your base are belong to us") >= 0
        self.is_leader = became_leader or took_over
        if self.is_leader:
            url = self.get_frontend().get_local_url("")
            reply = requests.get(url, auth=requests.auth.HTTPBasicAuth("root", self.passvoid))
            print(str(reply))
            if reply.status_code == 503:
                self.is_leader = False
        return self.is_leader

    @step
    def probe_leader(self):
        """talk to the frontends to find out whether its a leader or not."""
        # Should this be moved to the AF script?
        self.is_leader = False
        for instance in self.get_frontends():
            if instance.probe_if_is_leader():
                self.is_leader = True
        return self.is_leader

    @step
    def active_failover_detect_hosts(self):
        """detect hosts for the active failover"""
        self.check_that_instance_is_alive()
        # this is the way to detect the master starter...
        lfs = self.get_log_file()
        if lfs.find("Just became master") >= 0:
            self.is_master = True
        else:
            self.is_master = False
        regx = re.compile(r"Starting resilientsingle on port (\d*) .*")
        match = regx.search(lfs)
        if match is None:
            raise Exception(timestamp() + "Unable to get my host state! " + self.basedir + " - " + lfs)

        self.frontend_port = match.groups()[0]

    @step
    def active_failover_detect_host_now_follower(self):
        """detect whether we successfully respawned the instance,
        and it became a follower"""
        self.check_that_instance_is_alive()
        lfs = self.get_log_file()
        if lfs.find("resilientsingle up and running as follower") >= 0:
            self.is_master = False
            return True
        return False

    @step
    def search_for_warnings(self):
        """dump out instance args, and what could be fishy in my log"""
        log = str()
        print(self.arguments)
        if not self.log_file.exists():
            print(str(self.log_file) + " not there. Skipping search")
            return
        print(str(self.log_file))
        with self.log_file.open(errors="backslashreplace") as log_f:
            for line in log_f.readline():
                if "WARN" in line or "ERROR" in line:
                    print(line.rstrip())
                    log += line.rstrip()
        attach(log, "WARN or ERROR lines from starter log")

    @step
    def add_logfile_to_report(self):
        """Add starter log to allure report"""
        logfile = str(self.log_file)
        attach.file(logfile, "Starter log file", AttachmentType.TEXT)

    # pylint: disable=no-else-return
    def get_http_protocol(self):
        """get HTTP protocol for this starter(http/https)"""
        if self.cfg.ssl:
            return "https"
        else:
            return "http"

    @step
    def check_that_instance_is_alive(self):
        """Check that starter instance is alive"""
        if not self.instance.is_running():
            raise Exception(f"Starter instance is not running. Base directory: {str(self.basedir)}")
        if self.instance.status() == psutil.STATUS_ZOMBIE:
            raise Exception(f"Starter instance is a zombie. Base directory: {str(self.basedir)}")

    @step
    def check_that_starter_log_contains(self, substring: str):
        """check whether substring is present in the starter log"""
        if self.count_occurances_in_starter_log(substring) > 0:
            return
        else:
            raise Exception(
                f"Expected to find the following string: {substring}\n in this log file:\n{str(self.log_file)}"
            )

    def count_occurances_in_starter_log(self, substring: str):
        """count occurrences of a substring in the starter log"""
        number_of_occurances = self.get_log_file().count(substring)
        return number_of_occurances


class StarterNonManager(StarterManager):
    """this class is a dummy starter manager to work with similar interface"""

    # pylint: disable=dangerous-default-value disable=too-many-arguments
    def __init__(
        self,
        basecfg,
        install_prefix,
        instance_prefix,
        expect_instances,
        mode=None,
        port=None,
        jwt_str=None,
        moreopts=[],
    ):

        super().__init__(
            basecfg,
            install_prefix,
            instance_prefix,
            expect_instances,
            mode,
            port,
            jwt_str,
            moreopts,
        )

        if self.cfg.index >= len(self.cfg.frontends):
            self.cfg.index = 0
        inst = ArangodRemoteInstance(
            "coordinator",
            self.cfg.frontends[self.cfg.index].port,
            # self.cfg.localhost,
            self.cfg.frontends[self.cfg.index].ip,
            self.cfg.frontends[self.cfg.index].ip,
            Path("/"),
            self.cfg.passvoid,
            self.cfg.ssl,
            self.cfg.enterpise,
            self.cfg.version,
        )
        self.all_instances.append(inst)
        self.cfg.index += 1

    @step
    def run_starter(self, expect_to_fail=False):
        """fake run starter method"""

    @step
    def detect_instances(self):
        self.detect_arangosh_instances()

    @step
    def detect_instance_pids(self):
        if not self.get_frontends():
            print("no frontends?")
            raise Exception("foobar")

    def is_instance_up(self):
        return True
