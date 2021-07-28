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

from tools.asciiprint import print_progress as progress
from tools.timestamp import timestamp
import tools.loghelper as lh
from arangodb.instance import (
    ArangodInstance,
    ArangodRemoteInstance,
    SyncInstance,
    InstanceType,
    AfoServerState,
    get_instances_table
)
from arangodb.backup import HotBackupConfig, HotBackupManager
from arangodb.sh import ArangoshExecutor
from arangodb.imp import ArangoImportExecutor
from arangodb.restore import ArangoRestoreExecutor
from arangodb.bench import ArangoBenchManager

from reporting.reporting_utils import attach_table, step

ON_WINDOWS = (sys.platform == 'win32')


class StarterManager():
    """ manages one starter instance"""
    # pylint: disable=R0913 disable=R0902 disable=W0102 disable=R0915 disable=R0904 disable=E0202
    def __init__(self,
                 basecfg,
                 install_prefix, instance_prefix,
                 expect_instances,
                 mode=None, port=None, jwtStr=None, moreopts=[]):
        self.expect_instances = expect_instances
        self.expect_instances.sort()
        self.moreopts = moreopts
        self.cfg = copy.deepcopy(basecfg)
        if self.cfg.verbose:
            self.moreopts += ["--log.verbose=true"]
            # self.moreopts += ['--all.log', 'startup=debug']
        #self.moreopts += ["--all.log.level=arangosearch=trace"]
        #self.moreopts += ["--all.log.level=startup=trace"]
        #self.moreopts += ["--all.log.level=engines=trace"]

        #directories
        self.raw_basedir = install_prefix
        self.name = str(install_prefix / instance_prefix) # this is magic with the name function.
        self.basedir = self.cfg.base_test_dir / install_prefix / instance_prefix
        self.basedir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.basedir / "arangodb.log"

        #arg port - can be set - otherwise it is read from the log later
        self.starter_port = port
        if self.starter_port is not None:
            self.moreopts += ["--starter.port", "%d" % self.starter_port]

        self.hotbackup = []
        if (self.cfg.enterprise and
            semver.compare(self.cfg.version, "3.5.1") >=0 ):
            self.hotbackup = ['--all.rclone.executable',
                              self.cfg.real_sbin_dir / 'rclone-arangodb']

        if self.cfg.encryption_at_rest:
            self.keyfile = self.basedir / 'key.txt'
            # generate pseudo random key of length 32:
            self.keyfile.write_text((str(datetime.datetime.now()) * 5)[0:32])
            self.moreopts += ['--rocksdb.encryption-keyfile',
                             str(self.keyfile)]
        self.hb_instance = None
        self.hb_config = None
        # arg - jwtstr
        self.jwtfile = None
        self.jwt_header = None
        self.jwt_tokens = dict()
        if jwtStr:
            self.jwtfile = Path(str(self.basedir) + '_jwt')
            self.jwtfile.write_text(jwtStr)
            self.moreopts += ['--auth.jwt-secret', str(self.jwtfile)]
            self.get_jwt_header()

        self.passvoidfile = Path(str(self.basedir) + '_passvoid')
        # arg mode
        self.mode = mode
        if self.mode:
            self.moreopts += ["--starter.mode", self.mode]
            if self.mode == 'single':
                self.expect_instance_count = 1 # Only single server
            elif self.mode == 'activefailover':
                self.expect_instance_count = 2 # agent + server
            elif self.mode == 'cluster':
                self.expect_instance_count = 3 # agent + dbserver + coordinator
                if '--starter.local' in moreopts:
                     # full cluster on this starter:
                    self.expect_instance_count *= 3
                if '--starter.sync' in moreopts:
                    self.expect_instance_count += 2 # syncmaster + syncworker

        self.username = 'root'
        self.passvoid = ''

        self.instance = None #starter instance - PsUtil Popen child
        self.frontend_port = None #required for swith in active failover setup
        self.all_instances = [] # list of starters arangod child instances

        self.is_master = None
        self.is_leader = False
        self.arangosh = None
        self.arango_importer = None
        self.arango_restore = None
        self.arangobench = None
        self.executor = None # meaning?
        self.sync_master_port = None
        self.coordinator = None # meaning - port
        self.expect_instance_count = 1
        self.startupwait = 2
        self.supports_foxx_tests = True

        self.upgradeprocess = None

        self.arguments = [
            "--log.console=false",
            "--log.file=true",
            "--starter.data-dir={0.basedir}".format(self)
        ] + self.moreopts

    def __repr__(self):
        return str(get_instances_table(self.get_instance_essentials()))

    def name(self):
        """ name of this starter """
        return str(self.name)

    def get_frontends(self):
        """ get the frontend URLs of this starter instance """
        ret = []
        for i in self.all_instances:
            if i.is_frontend():
                ret.append(i)
        return ret

    def get_dbservers(self):
        """ get the list of dbservers managed by this starter """
        ret = []
        for i in self.all_instances:
            if i.is_dbserver():
                ret.append(i)
        return ret

    def get_agents(self):
        """ get the list of agents managed by this starter """
        ret = []
        for i in self.all_instances:
            if i.instance_type == InstanceType.AGENT:
                ret.append(i)
        return ret

    def get_sync_masters(self):
        """ get the list of arangosync masters managed by this starter """
        ret = []
        for i in self.all_instances:
            if i.instance_type == InstanceType.SYNCMASTER:
                ret.append(i)
        return ret

    def get_frontend(self):
        """ get the first frontendhost of this starter """
        servers = self.get_frontends()
        assert servers, "starter: don't have instances!"
        return servers[0]

    def get_dbserver(self):
        """ get the first dbserver of this starter """
        servers = self.get_dbservers()
        assert servers, "starter: don't have instances!"
        return servers[0]

    def get_agent(self):
        """ get the first agent of this starter """
        servers = self.get_agents()
        assert servers, "starter: have no instances!"
        return servers[0]

    def get_sync_master(self):
        """ get the first arangosync master of this starter """
        servers = self.get_sync_masters()
        assert servers, "starter: don't have instances!"
        return servers[0]

    def have_this_instance(self, instance):
        """ detect whether this manager manages instance """
        for i in self.all_instances:
            if i == instance:
                print("YES ITS ME!")
                return True
        print("NO S.B. ELSE")
        return False

    def get_instance_essentials(self):
        """ get the essentials of all instances controlled by this starter """
        ret = []
        for instance in self.all_instances:
            ret.append(instance.get_essentials())
        return ret

    def show_all_instances(self):
        """ print all instances of this starter to the user """
        if not self.all_instances:
            logging.error("%s: no instances detected", self.name)
            return
        instances = ""
        for instance in self.all_instances:
            instances += " - {0.name} (pid: {0.pid})".format(instance)
        logging.info("arangod instances for starter: %s - %s", self.name, instances)

    @step("Run starter")
    def run_starter(self):
        """ launch the starter for this instance"""
        logging.info("running starter " + self.name)
        args = [self.cfg.bin_dir / 'arangodb'] + self.hotbackup + self.arguments
        lh.log_cmd(args)
        self.instance = psutil.Popen(args)
        self.wait_for_logfile()

    @step("Attach to a running starter")
    def attach_running_starter(self):
        """ somebody else is running the party, but we also want to have a look """
        #pylint disable=W0703
        match_str = "--starter.data-dir={0.basedir}".format(self)
        if self.passvoidfile.exists():
            self.passvoid = self.passvoidfile.read_text(errors='backslashreplace')
        for process in psutil.process_iter(['pid', 'name']):
            try:
                name = process.name()
                if name.startswith('arangodb'):
                    process = psutil.Process(process.pid)
                    if any(match_str in s for s in process.cmdline()):
                        print(process.cmdline())
                        print('attaching ' + str(process.pid))
                        self.instance = process
                        return
            except psutil.NoSuchProcess as ex:
                logging.error(ex)
        raise Exception("didn't find a starter for " + match_str)

    @step("Set JWT file")
    def set_jwt_file(self, filename):
        """ some scenarios don't want to use the builtin jwt generation from the manager """
        self.jwtfile = filename

    def get_jwt_token_from_secret_file(self, filename):
        """ retrieve token from the JWT secret file which is cached for the future use """
        if filename in self.jwt_tokens.keys():
            # token for that file was checked already.
            return self.jwt_tokens[filename]

        cmd = [self.cfg.bin_dir / 'arangodb',
               'auth', 'header',
               '--auth.jwt-secret', str(filename)]
        print(cmd)
        jwt_proc = psutil.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (header, err) = jwt_proc.communicate()
        jwt_proc.wait()
        if len(str(err)) > 3:
            raise Exception("error invoking the starter "
                            "to generate the jwt header token! " + str(err))
        if len(str(header).split(' ')) != 3:
            raise Exception("failed to parse the output"
                            " of the header command: " + str(header))

        self.jwt_tokens[filename] = str(header).split(' ')[2].split('\\')[0]
        return self.jwt_tokens[filename]

    def get_jwt_header(self):
        """ return jwt header from current installation """
        if self.jwt_header:
            return self.jwt_header
        self.jwt_header = self.get_jwt_token_from_secret_file(str(self.jwtfile))
        return self.jwt_header

    @step
    def set_passvoid(self, passvoid, write_to_server=True):
        """ set the passvoid to the managed instance """
        if write_to_server:
            print("Provisioning passvoid " + passvoid)
            self.arangosh.js_set_passvoid('root', passvoid)
            self.passvoidfile.write_text(passvoid)
        self.passvoid = passvoid
        for i in self.all_instances:
            if i.is_frontend():
                i.set_passvoid(passvoid)
        self.cfg.passvoid = passvoid

    def get_passvoid(self):
        """ get the passvoid to the managed instance """
        return self.passvoid

    @step("Send HTTP request")
    def send_request(self, instance_type, verb_method,
                     url, data=None, headers={}, timeout = None):
        """ send an http request to the instance """
        http_client.HTTPConnection.debuglevel = 1

        results = []
        for instance in self.all_instances:
            if instance.instance_type == instance_type:
                if instance.detect_gone():
                    print("Instance to send request to already gone: " + repr(instance))
                else:
                    headers ['Authorization'] = 'Bearer ' + str(self.get_jwt_header())
                    base_url = instance.get_public_plain_url()
                    reply = verb_method(
                        'http://' + base_url + url,
                        data=data,
                        headers=headers,
                        allow_redirects=False,
                        timeout=timeout
                    )
                    # print(reply.text)
                    results.append(reply)
        http_client.HTTPConnection.debuglevel = 0
        return results

    @step("Crash managed instances and the starter")
    def crash_instances(self):
        """ make all managed instances plus the starter itself crash. """
        try:
            if (self.instance.status() == psutil.STATUS_RUNNING or
                self.instance.status() == psutil.STATUS_SLEEPING):
                print("generating coredump for " + str(self.instance))
                psutil.Popen(['gcore', str(self.instance.pid)], cwd=self.basedir).wait()
                self.kill_instance()
            else:
                print("NOT generating coredump for " + str(self.instance))
        except psutil.NoSuchProcess:
            logging.info("instance already dead: " + str(self.instance))

        for instance in self.all_instances:
            instance.crash_instance()

    def is_instance_running(self):
        """ check whether this is still running"""
        try:
            self.instance.wait(timeout=1)
        except psutil.TimeoutExpired:
            pass
        return self.instance.is_running()

    @step("Wait for our instance to create a logfile")
    def wait_for_logfile(self):
        """ wait for our instance to create a logfile """
        counter = 0
        keep_going = True
        logging.info('Looking for log file.\n')
        while keep_going:
            if not self.instance.is_running():
                raise Exception(timestamp() +
                                "my instance is gone!" + self.basedir)
            if counter == 20:
                raise Exception("logfile did not appear: " + str(self.log_file))
            counter += 1
            logging.info('counter = ' + str(counter))
            if self.log_file.exists():
                logging.info('Found: '+ str(self.log_file) + '\n')
                keep_going = False
            time.sleep(1)

    @step("Wait until upgrade is finished")
    def wait_for_upgrade_done_in_log(self, timeout=120):
        """ in single server mode the 'upgrade' commander exits before
            the actual upgrade is finished. Hence we need to look into
            the logfile of the managing starter if it thinks its finished.
        """
        keep_going = True
        logging.info('Looking for "Upgrading done" in the log file.\n')
        while keep_going:
            text = self.get_log_file()
            pos = text.find('Upgrading done.')
            keep_going = pos == -1
            if keep_going:
                time.sleep(1)
            progress('.')
            timeout -= 1
            if timeout <= 0:
                raise TimeoutError("upgrade of leader follower not found on time")
        for instance in self.all_instances:
            instance.wait_for_shutdown()

    @step
    def is_instance_up(self):
        """ check whether all spawned arangods are fully bootet"""
        logging.debug("checking if starter instance booted: "
                      + str(self.basedir))
        if not self.instance.is_running():
            logging.error("Starter Instance {0.name} is gone!".format(self))
            sys.exit(0)

        # if the logfile contains up and running we are fine
        lfs = self.get_log_file()
        regx = re.compile(r'(\w*) up and running ')
        for line in lfs.splitlines():
            match = regx.search(line)
            if  match:
                groups = match.groups()
                if len(groups) == 1 and groups[0] == 'agent':
                    continue
                return True

        return False

    @step("Terminate instance")
    def terminate_instance(self):
        """ terminate the instance of this starter
            (it should kill all its managed services)"""

        lh.subsubsection("terminating instances for: " + str(self.name))
        logging.info("StarterManager: Terminating starter instance: %s",
                     str(self.arguments))


        logging.info("This should terminate all child processes")
        self.instance.terminate()
        logging.info("StarterManager: waiting for process to exit")
        exit_code = self.instance.wait()
        if exit_code != 0:
            raise Exception("Starter exited with %d" % exit_code)

        old_log = self.basedir / "arangodb.log.old"
        logging.info("StarterManager: done - moving logfile from %s to %s",
                     str(self.log_file), str(old_log))
        if old_log.exists():
            old_log.unlink()
        self.log_file.rename(old_log)

        for instance in self.all_instances:
            instance.rename_logfile()
            instance.detect_gone()
        # Clear instances as they have been stopped and the logfiles
        # have been moved.
        self.is_leader = False
        self.all_instances = []

    @step("Kill instance")
    def kill_instance(self):
        """ kill the instance of this starter
            (it won't kill its managed services)"""
        logging.info("StarterManager: Killing: %s", str(self.arguments))
        self.instance.kill()
        try:
            logging.info(str(self.instance.wait(timeout=45)))
        except Exception as ex:
            raise Exception("Failed to KILL the starter instance? " +
                            repr(self)) from ex

        logging.info("StarterManager: Instance now dead.")

    @step("Replace binary for upgrade")
    def replace_binary_for_upgrade(self, new_install_cfg):
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
        self.cfg.set_directories(new_install_cfg)
        if self.cfg.hot_backup:
            self.hotbackup = [
                '--all.rclone.executable',
                self.cfg.real_sbin_dir / 'rclone-arangodb']
        logging.info("StarterManager: Killing my instance [%s]",
                     str(self.instance.pid))
        self.kill_instance()
        self.detect_instance_pids_still_alive()
        self.respawn_instance()
        logging.info("StarterManager: respawned instance as [%s]",
                     str(self.instance.pid))

    @step("Kill all arangosync instances")
    def kill_sync_processes(self):
        """ kill all arangosync instances we posses """
        for i in self.all_instances:
            if i.is_sync_instance():
                logging.info("manually killing syncer: " + str(i.pid))
                i.terminate_instance()

    @step("Perform a rolling upgrade using starter")
    def command_upgrade(self):
        """
        we use a starter, to tell daemon starters to perform the rolling upgrade
        """
        args = [
            self.cfg.bin_dir / 'arangodb',
            'upgrade',
            '--starter.endpoint',
            'http://127.0.0.1:' + str(self.get_my_port())
        ]
        logging.info("StarterManager: Commanding upgrade %s", str(args))
        self.upgradeprocess = psutil.Popen(args,
                                           #stdout=subprocess.PIPE,
                                           #stdin=subprocess.PIPE,
                                           #stderr=subprocess.PIPE,
                                           universal_newlines=True)

    @step("Wait for the upgrade commanding starter to finish")
    def wait_for_upgrade(self, timeout=60):
        """ wait for the upgrade commanding starter to finish """
        #for line in self.upgradeprocess.stderr:
        #    ascii_print(line)
        ret = None
        try:
            ret = self.upgradeprocess.wait(timeout=timeout)
        except psutil.TimeoutExpired as timeout_ex:
            logging.error("StarterManager: Upgrade command [%s] didn't finish in time: %d %s",
                          str(self.basedir),
                          timeout,
                          str(timeout_ex))
            raise timeout_ex
        logging.info("StarterManager: Upgrade command [%s] exited: %s",
                     str(self.basedir),
                     str(ret))
        if ret != 0:
            raise Exception("Upgrade process exited with non-zero reply")

    @step("Wait for the server to restart after the \"restore\" command")
    def wait_for_restore(self):
        """
        tries to wait for the server to restart after the 'restore' command
        """
        for node in  self.all_instances:
            if node.instance_type in [
                    InstanceType.RESILIENT_SINGLE,
                    InstanceType.SINGLE,
                    InstanceType.DBSERVER]:
                node.detect_restore_restart()

    @step("Wait until all instances reply with 200 to \"api/version\"")
    def tcp_ping_nodes(self):
        """
        tries to wait for the server to restart after the 'restore' command
        """
        for node in  self.all_instances:
            if node.instance_type in [
                    InstanceType.RESILIENT_SINGLE,
                    InstanceType.SINGLE,
                    InstanceType.DBSERVER]:
                node.check_version_request(20.0)

    @step("Restart the starter instance")
    def respawn_instance(self):
        """ restart the starter instance after we killed it eventually """
        args = [
            self.cfg.bin_dir / 'arangodb'
        ] + self.hotbackup + self.arguments

        logging.info("StarterManager: respawning instance %s", str(args))
        self.instance = psutil.Popen(args)
        self.wait_for_logfile()

    @step("Wait until SUT replies with a 200 to /_api/version")
    def wait_for_version_reply(self):
        """ wait for the SUT reply with a 200 to /_api/version """
        frontends = self.get_frontends()
        for frontend in frontends:
            # we abuse this function:
            while frontend.get_afo_state() != AfoServerState.LEADER:
                progress(".")
                time.sleep(0.1)

    @step("Run command in arangosh")
    def execute_frontend(self, cmd, verbose=True):
        """ use arangosh to run a command on the frontend arangod"""
        return self.arangosh.run_command(cmd, verbose)

    def get_frontend_port(self):
        """ get the port of the arangod which is coordinator etc."""
        if self.frontend_port:
            return self.frontend_port
        return self.get_frontend().port

    def get_my_port(self):
        """ find out my frontend port """
        if self.starter_port is not None:
            return self.starter_port

        where = -1
        tries = 10
        while where == -1 and tries:
            tries -= 1
            lfcontent = self.get_log_file()
            where = lfcontent.find('ArangoDB Starter listening on')
            if where != -1:
                where = lfcontent.find(':', where)
                if where != -1:
                    end = lfcontent.find(' ', where)
                    port = lfcontent[where + 1: end]
                    self.starter_port = port
                    assert int(port), "port cannot be converted to int!"
                    return port
            logging.info('retrying logfile')
            time.sleep(1)
        logging.error("could not get port form: " + self.log_file)
        sys.exit(1)

    def get_sync_master_port(self):
        """ get the port of a syncmaster arangosync"""
        self.sync_master_port = None
        pos = None
        sm_port_text = 'Starting syncmaster on port'
        sw_text = 'syncworker up and running'
        worker_count = 0
        logging.info('detecting sync master port')
        while worker_count < 3 and self.is_instance_running():
            progress('%')
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
            self.sync_master_port = int(lfs[pos : pos+4])
        return self.sync_master_port

    @step
    def get_log_file(self):
        """ fetch the logfile of this starter"""
        return self.log_file.read_text(errors='backslashreplace')

    def read_db_logfile(self):
        """ get the logfile of the dbserver instance"""
        server = self.get_dbserver()
        assert server.logfile.exists(), "don't have logfile?"
        return server.logfile.read_text(errors='backslashreplace')

    @step
    def read_agent_logfile(self):
        """ get the agent logfile of this instance"""
        server = self.get_agent()
        assert server.logfile.exists(), "don't have logfile?"
        return server.logfile.read_text(errors='backslashreplace')

    @step("Detect instances")
    def detect_instances(self):
        """ see which arangods where spawned and inspect their logfiles"""
        lh.subsection("Instance Detection for {0.name}".format(self))
        self.all_instances = []
        logging.debug("waiting for frontend")
        logfiles = set() #logfiles that can be used for debugging

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
                    #logging.debug("f: " + root + os.path.sep + onefile)
                    if onefile.endswith("log"):
                        logfiles.add(str(Path(root) / onefile))

                for name in dirs:
                    #logging.debug("d: " + root + os.path.sep + name)
                    match = None
                    instance_class = None
                    if name.startswith('sync'):
                        match = re.match(r'(syncmaster|syncworker)(\d*)', name)
                        instance_class = SyncInstance
                    else:
                        match = re.match(
                            r'(agent|coordinator|dbserver|resilientsingle|single)(\d*)',
                            name)
                        instance_class = ArangodInstance
                    # directory = self.basedir / name
                    if match:
                        # we may see a `local-slave-*` directory inbetween,
                        # hence we need to choose the current directory not
                        # the starter toplevel dir for this:
                        instance = instance_class(match.group(1),
                                                  match.group(2),
                                                  self.cfg.localhost,
                                                  self.cfg.publicip,
                                                  Path(root) / name,
                                                  self.passvoid)
                        instance.wait_for_logfile(tries)
                        instance.detect_pid(
                            ppid=self.instance.pid,
                            full_binary_path=self.cfg.real_sbin_dir,
                            offset=0)
                        detected_instances.append(instance.instance_type)
                        self.all_instances.append(instance)

            print(self.expect_instances)
            detected_instances.sort()
            print(detected_instances)
            attach(str(self.expect_instances), "Expected instances")
            attach(str(detected_instances), "Detected instances")
            if ((self.expect_instances != detected_instances) or
                (not self.get_frontends())):
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
            logging.error("if that does not help try to delete: " +
                          str(self.basedir))
            sys.exit(1)

        self.show_all_instances()

    @step
    def detect_instance_pids(self):
        """ detect the arangod instance PIDs"""
        for instance in self.all_instances:
            instance.detect_pid(ppid=self.instance.pid,
                                full_binary_path=self.cfg.real_sbin_dir,
                                offset=0)

        self.show_all_instances()
        self.detect_arangosh_instances()

    @step
    def detect_fatal_errors(self):
        """ scan all instances for `FATAL` statements """
        for instance in self.all_instances:
            instance.detect_fatal_errors()

    @step("Detect arangosh instances")
    def detect_arangosh_instances(self):
        """
        gets the arangosh instance to speak to the frontend of this starter
        """
        if self.arangosh is None:
            self.cfg.port = self.get_frontend_port()

            self.arangosh = ArangoshExecutor(self.cfg, self.get_frontend())
            self.arango_importer = ArangoImportExecutor(self.cfg, self.get_frontend())
            self.arango_restore = ArangoRestoreExecutor(self.cfg, self.get_frontend())
            if self.cfg.hot_backup:
                self.cfg.passvoid = self.passvoid
                self.hb_instance = HotBackupManager(
                    self.cfg,
                    self.raw_basedir,
                    self.cfg.base_test_dir / self.raw_basedir,
                    self.get_frontend())
                self.hb_config = HotBackupConfig(
                    self.cfg,
                    self.raw_basedir,
                    self.cfg.base_test_dir / self.raw_basedir)

    @step("Launch arangobench")
    def launch_arangobench(self, testacse_no, moreopts = []):
        """ launch an arangobench instance to the frontend of this starter """
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
            logging.error("Not all instances are alive. "
                          "The following are not running: %s",
                          str(missing_instances))
            #if self.abort_on_error:
            #    logging.error("exiting")
            #    sys.exit(1)
            raise Exception("instances missing: " + str(missing_instances))
        instances_table = get_instances_table(self.get_instance_essentials())
        logging.info("All arangod instances still running: \n%s",
                     str(instances_table))
        attach_table(instances_table, "Instances table")


    @step
    def maintainance(self, on_off, instance_type):
        """ enables / disables maintainance mode """
        print(("enabling" if on_off else "disabling") + " Maintainer mode")
        while True:
            reply = self.send_request(instance_type,
                                      requests.put,
                                      "/_admin/cluster/maintenance",
                                      '"on"' if on_off else '"off"')
            print("Reply: " + str(reply[0].text))
            if reply[0].status_code == 200:
                return
            time.sleep(3)

    @step
    def detect_leader(self):
        """ in active failover detect whether we run the leader"""
        # Should this be moved to the AF script?
        lfs = self.read_db_logfile()

        became_leader = lfs.find('Became leader in') >= 0
        took_over = lfs.find('Successful leadership takeover:'
                             ' All your base are belong to us') >= 0
        self.is_leader = (became_leader or took_over)
        if self.is_leader:
            url = self.get_frontend().get_local_url('')
            reply = requests.get(url, auth=requests.auth.HTTPBasicAuth('root', self.passvoid))
            print(str(reply))
            if reply.status_code == 503:
                self.is_leader = False
        return self.is_leader

    @step
    def probe_leader(self):
        """ talk to the frontends to find out whether its a leader or not. """
        # Should this be moved to the AF script?
        self.is_leader = False
        for instance in self.get_frontends():
            if instance.probe_if_is_leader():
                self.is_leader = True
        return self.is_leader

    @step
    def active_failover_detect_hosts(self):
        """ detect hosts for the active failover """
        if not self.instance.is_running():
            raise Exception(timestamp()
                            + "my instance is gone! "
                            + self.basedir)
        # this is the way to detect the master starter...
        lfs = self.get_log_file()
        if lfs.find('Just became master') >= 0:
            self.is_master = True
        else:
            self.is_master = False
        regx = re.compile(r'Starting resilientsingle on port (\d*) .*')
        match = regx.search(lfs)
        if match is None:
            raise Exception(timestamp()
                            + "Unable to get my host state! "
                            + self.basedir
                            + " - " + lfs)

        self.frontend_port = match.groups()[0]

    @step
    def active_failover_detect_host_now_follower(self):
        """ detect whether we successfully respawned the instance,
            and it became a follower"""
        if not self.instance.is_running():
            raise Exception(timestamp()
                            + "my instance is gone! "
                            + self.basedir)
        lfs = self.get_log_file()
        if lfs.find('resilientsingle up and running as follower') >= 0:
            self.is_master = False
            return True
        return False

    @step("Look for warnings or errors in starter logs")
    def search_for_warnings(self):
        """ dump out instance args, and what could be fishy in my log """
        log = str()
        print(self.arguments)
        if not self.log_file.exists():
            print(str(self.log_file) + " not there. Skipping search")
            return
        print(str(self.log_file))
        with self.log_file.open(errors='backslashreplace') as log_f:
            for line in log_f.readline():
                if ('WARN' in line or
                    'ERROR' in line):
                    print(line.rstrip())
                    log += line.rstrip()
        attach(log, "WARN or ERROR lines from starter log")

class StarterNonManager(StarterManager):
    """ this class is a dummy starter manager to work with similar interface """
    # pylint: disable=W0102 disable=R0913
    def __init__(self,
                 basecfg,
                 install_prefix, instance_prefix,
                 expect_instances,
                 mode=None, port=None, jwtStr=None, moreopts=[]):

        super().__init__(
            basecfg,
            install_prefix, instance_prefix,
            expect_instances,
            mode, port, jwtStr, moreopts)

        if basecfg.index >= len(basecfg.frontends):
            basecfg.index = 0
        inst = ArangodRemoteInstance('coordinator',
                                     basecfg.frontends[basecfg.index].port,
                                     # self.cfg.localhost,
                                     basecfg.frontends[basecfg.index].ip,
                                     basecfg.frontends[basecfg.index].ip,
                                     Path('/'),
                                     self.cfg.passvoid)
        self.all_instances.append(inst)
        basecfg.index += 1

    @step
    def run_starter(self):
        pass

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
