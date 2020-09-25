#!/usr/bin/env python
""" Manage one instance of the arangodb starter
    to crontroll multiple arangods
"""

import copy
import logging
import os
import re
import signal
import subprocess
import sys
import time

from pathlib import Path
# from typing import List, Dict, NamedTuple

import psutil

import http.client as http_client
import requests
from tools.asciiprint import ascii_print, print_progress as progress
from tools.timestamp import timestamp
from arangodb.instance import ArangodInstance, ArangodRemoteInstance, SyncInstance, InstanceType, AfoServerState
from arangodb.backup import HotBackupConfig, HotBackupManager
from arangodb.sh import ArangoshExecutor
import tools.loghelper as lh

ON_WINDOWS = (sys.platform == 'win32')


class StarterManager():
    """ manages one starter instance"""
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

        #directories
        self.raw_basedir = install_prefix
        self.name = str(install_prefix / instance_prefix)
        self.basedir = self.cfg.baseTestDir / install_prefix / instance_prefix
        self.log_file = self.basedir / "arangodb.log"

        #arg port - can be set - otherwise it is read from the log later
        self.starter_port = port
        if self.starter_port is not None:
            self.moreopts += ["--starter.port", "%d" % self.starter_port]

        self.hotbackup = []
        if self.cfg.enterprise:
            self.hotbackup = ['--all.rclone.executable', self.cfg.sbin_dir / 'rclone-arangodb']

        # arg - jwtstr
        self.jwtfile = None
        self.jwt_header = None
        if jwtStr:
            self.basedir.mkdir(parents=True, exist_ok=True)
            self.jwtfile = self.basedir / 'jwt'
            self.jwtfile.write_text(jwtStr)
            self.moreopts += ['--auth.jwt-secret', str(self.jwtfile)]
            self.get_jwt_header()

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
                    self.expect_instance_count *= 3 # full cluster on this starter
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
        self.executor = None # meaning?
        self.sync_master_port = None
        self.coordinator = None # meaning - port
        self.expect_instance_count = 1
        self.startupwait = 2

        self.upgradeprocess = None

        self.arguments = [
            "--log.console=false",
            "--log.file=true",
            "--starter.data-dir={0.basedir}".format(self)
        ] + self.moreopts

    def __repr__(self):
        return """
===================================================
Starter {0.name}
    user            {0.username}
    password        {0.passvoid}
    -----------------------------------------------
    all_instances   {0.all_instances}
    -----------------------------------------------
    frontends       {1}
===================================================
""".format(self, self.get_frontends())

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
            if i.type == InstanceType.agent:
                ret.append(i)
        return ret

    def get_frontend(self):
        """ get the first frontendhost of this starter """
        servers = self.get_frontends()
        assert servers
        return servers[0]

    def get_dbserver(self):
        """ get the first dbserver of this starter """
        servers = self.get_dbservers()
        assert servers
        return servers[0]

    def get_agent(self):
        """ get the first agent of this starter """
        servers = self.get_agents()
        assert servers
        return servers[0]

    def show_all_instances(self):
        """ print all instances of this starter to the user """
        logging.info("arangod instances for starter: " + self.name)
        if not self.all_instances:
            logging.info("no instances detected")
            return

        logging.info("detected instances: ----")
        for instance in self.all_instances:
            print(" - {0.name} (pid: {0.pid})".format(instance))
        logging.info("------------------------")


    def run_starter(self):
        """ launch the starter for this instance"""
        logging.info("running starter " + self.name)
        args = [self.cfg.bin_dir / 'arangodb'] + self.hotbackup + self.arguments
        lh.log_cmd(args)
        self.instance = psutil.Popen(args)
        self.wait_for_logfile()

    def get_jwt_header(self):
        if self.jwt_header:
            return self.jwt_header
        cmd = [self.cfg.bin_dir / 'arangodb',
               'auth', 'header',
               '--auth.jwt-secret', str(self.jwtfile)]
        print(cmd)
        r = psutil.Popen(cmd,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (header, err) = r.communicate()
        r.wait()
        print(err)
        print(len(str(err)))
        if len(str(err)) > 3:# TODO Y?
            raise Exception("error invoking the starter to generate the jwt header token! " + str(err))
        if len(str(header).split(' ')) != 3:
            raise Exception("failed to parse the output of the header command: " + str(header))
        self.jwt_header = str(header).split(' ')[2].split('\\')[0]

    def send_request(self, instance_type, verb_method, url, data=None, headers={}):
        http_client.HTTPConnection.debuglevel = 1

        headers ['Authorization'] = 'Bearer '+ self.jwt_header
        results = []
        for instance in self.all_instances:
            if instance.type == instance_type:
                base_url = instance.get_public_plain_url()
                reply = verb_method('http://' + base_url + url, data=data, headers=headers)
                print(reply.text)
                results.append(reply)
        return results

    def is_instance_running(self):
        """ check whether this is still running"""
        try:
            self.instance.wait(timeout=1)
        except:
            pass
        return self.instance.is_running()

    def wait_for_logfile(self):
        counter = 0
        keepGoing = True
        logging.info('Looking for log file.\n')
        while keepGoing:
            if not self.instance.is_running():
                raise Exception(timestamp() + "my instance is gone!" + self.basedir)
            if (counter == 20):
                raise Exception("logfile did not appear: " + str(self.log_file))
            counter += 1
            logging.info('counter = ' + str(counter))
            if self.log_file.exists():
                logging.info('Found: '+ str(self.log_file) + '\n')
                keepGoing = False
            time.sleep(1)

    def wait_for_upgrade_done_in_log(self):
        """ in single server mode the 'upgrade' commander exits before
            the actual upgrade is finished. Hence we need to look into
            the logfile of the managing starter if it thinks its finished.
        """
        counter = 0
        keepGoing = True
        logging.info('Looking for "Upgrading done" in the log file.\n')
        while keepGoing:
            text = self.get_log_file()
            keepGoing = text.find('Upgrading done.') >= 0
            progress('.')
        for instance in self.all_instances:
            instance.wait_for_shutdown()

    def is_instance_up(self):
        """ check whether all spawned arangods are fully bootet"""
        logging.debug("checking if starter instance booted: " + str(self.basedir))
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

    def terminate_instance(self):
        """ terminate the instance of this starter
            (it should kill all its managed services)"""

        lh.subsubsection("terminating instances for: " + str(self.name))
        logging.info("StarterManager: Terminating starter instance: %s", str(self.arguments))


        logging.info("This should terminate all child processes")
        self.instance.terminate()
        logging.info("StarterManager: waiting for process to exit")
        self.instance.wait()

        logging.info("StarterManager: done - moving logfile from %s to %s",
                     str(self.log_file),
                     str(self.basedir / "arangodb.log.old"))
        self.log_file.rename(self.basedir / "arangodb.log.old")

        for instance in self.all_instances:
            instance.rename_logfile()
            instance.detect_gone()
        # Clear instances as they have been stopped and the logfiles
        # have been moved.
        self.is_leader = False
        self.all_instances = []

    def kill_instance(self):
        """ kill the instance of this starter
            (it won't kill its managed services)"""
        logging.info("StarterManager: Killing: %s", str(self.arguments))
        self.instance.kill()
        try:
            logging.info(str(self.instance.wait(timeout=45)))
        except:
            raise Exception("Failed to KILL the starter instance? " + repr(self))

        logging.info("StarterManager: Instance now dead.")

    def replace_binary_for_upgrade(self, new_install_cfg):
        """
          - replace the parts of the installation with information after an upgrade
          - kill the starter processes of the old version
          - revalidate that the old arangods are still running and alive
          - replace the starter binary with a new one. this has not yet spawned any children
        """
        # On windows the install prefix may change, since we can't overwrite open files:
        self.cfg.set_directories(new_install_cfg)
        if self.cfg.enterprise:
            self.hotbackup = ['--all.rclone.executable', self.cfg.sbin_dir / 'rclone-arangodb']
        logging.info("StarterManager: Killing my instance [%s]", str(self.instance.pid))
        self.kill_instance()
        self.detect_instance_pids_still_alive()
        self.respawn_instance()
        logging.info("StarterManager: respawned instance as [%s]", str(self.instance.pid))

    def kill_sync_processes(self):
        """ kill all arangosync instances we posses """
        for i in self.all_instances:
            if i.is_sync_instance():
                logging.info("manually killing syncer: " + str(i.pid))
                i.terminate_instance()

    def command_upgrade(self):
        """ we use a starter, to tell daemon starters to perform the rolling upgrade """
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
                                           stderr=subprocess.PIPE,
                                           universal_newlines=True)

    def wait_for_upgrade(self):
        """ wait for the upgrade commanding starter to finish """
        for line in self.upgradeprocess.stderr:
            ascii_print(line)
        ret = self.upgradeprocess.wait()
        logging.info("StarterManager: Upgrade command exited: %s", str(ret))
        if ret != 0:
            raise Exception("Upgrade process exited with non-zero reply")

    def wait_for_restore(self):
        """ tries to wait for the server to restart after the 'restore' command """
        for node in  self.all_instances:
            if node.type in [InstanceType.resilientsingle,
                             InstanceType.single,
                             InstanceType.dbserver]:
                node.detect_restore_restart()

    def respawn_instance(self):
        """ restart the starter instance after we killed it eventually """
        args = [
            self.cfg.bin_dir / 'arangodb'
        ] + self.hotbackup + self.arguments

        logging.info("StarterManager: respawning instance %s", str(args))
        self.instance = psutil.Popen(args)
        self.wait_for_logfile()

    def wait_for_version_reply(self):
        """ wait for the SUT reply with a 200 to /_api/version """
        frontends = self.get_frontends()
        for frontend in frontends:
            # we abuse this function:
            while frontend.get_afo_state() != AfoServerState.leader:
                progress(".")
                time.sleep(0.1)

    def execute_frontend(self, cmd, verbose=True):
        """ use arangosh to run a command on the frontend arangod"""
        return self.arangosh.run_command(cmd, verbose)

    def get_frontend_port(self):
        """ get the port of the arangod which is coordinator etc."""
        #FIXME This looks unreliable to me, especially when terminating
        #      instances. How will the variable get updated?
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
                    assert int(port) #assert that we can convert to int
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

    def get_log_file(self):
        """ fetch the logfile of this starter"""
        return self.log_file.read_text()

    def read_db_logfile(self):
        """ get the logfile of the dbserver instance"""
        server = self.get_dbserver()
        assert server.logfile.exists()
        return server.logfile.read_text()

    def read_agent_logfile(self):
        """ get the agent logfile of this instance"""
        server = self.get_agent()
        assert server.logfile.exists()
        return server.logfile.read_text()

    def detect_instances(self):
        """ see which arangods where spawned and inspect their logfiles"""
        lh.subsection("Instance Detection for {0.name}".format(self))
        self.all_instances = []
        logging.debug("waiting for frontend")
        logfiles = set() #logfiles that can be used for debugging

         # the more instances we expect to spawn the more patient:
        tries = 10 * self.expect_instance_count

        # Wait for forntend to become alive.
        allInstancesUp = False
        while not allInstancesUp and tries:
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
                    directory = self.basedir / name
                    if match:
                        # we may see a `local-slave-*` directory inbetween, hence we need to
                        # choose the current directory not the starter toplevel dir for this:
                        instance = instance_class(match.group(1),
                                                  match.group(2),
                                                  self.cfg.localhost,
                                                  self.cfg.publicip,
                                                  Path(root) / name)
                        instance.wait_for_logfile(tries)
                        instance.detect_pid(ppid=self.instance.pid, full_binary_path = self.cfg.real_sbin_dir)
                        detected_instances.append(instance.type)
                        self.all_instances.append(instance)

            print(self.expect_instances)
            detected_instances.sort()
            print(detected_instances)
            if ((self.expect_instances != detected_instances) or
                (not self.get_frontends())):
                tries -= 1
                time.sleep(5)
            else:
                allInstancesUp = True

        if not self.get_frontends():
            print()
            logging.error("STARTER FAILED TO SPAWN ARANGOD")
            self.show_all_instances()
            logging.error("can not continue without frontend instance")
            logging.error("please check logs in" + str(self.basedir))
            for logf in logfiles:
                logging.debug(logf)
            logging.error("if that does not help try to delete: " + str(self.basedir))
            sys.exit(1)

        self.show_all_instances()

    def detect_instance_pids(self):
        # TODO: Do we stil need the log.py or should it be removed
        """ detect the arangod instance PIDs"""
        for instance in self.all_instances:
            instance.detect_pid(ppid=self.instance.pid, full_binary_path=self.cfg.real_sbin_dir)

        self.show_all_instances()
        self.detect_arangosh_instances()

    def detect_arangosh_instances(self):
        if self.arangosh is None:
            self.cfg.port = self.get_frontend_port()
            
            self.arangosh = ArangoshExecutor(self.cfg, self.get_frontend())
            if self.cfg.enterprise:
                self.hb_instance = HotBackupManager(self.cfg, self.raw_basedir, self.cfg.baseTestDir / self.raw_basedir)
                self.hb_config = HotBackupConfig(self.cfg, self.raw_basedir, self.cfg.baseTestDir / self.raw_basedir)

    def detect_instance_pids_still_alive(self):
        """ detecting whether the processes the starter spawned are still there """
        missing_instances = []
        running_pids = psutil.pids()
        for instance in self.all_instances:
            if instance.pid not in running_pids:
                missing_instances.append(instance)

        if len(missing_instances) > 0:
            logging.error("Not all instances are alive. The following are not running: %s",
                          str(missing_instances))
            logging.error("exiting")
            sys.exit(1)
            #raise Exception("instances missing: " + str(missing_instances))
        else:
            logging.info("All arangod instances still running: %s", str(self.all_instances))

    def detect_leader(self):
        """ in active failover detect whether we run the leader"""
        # Should this be moved to the AF script?
        lfs = self.read_db_logfile()

        became_leader = lfs.find('Became leader in') >= 0
        took_over = lfs.find('Successful leadership takeover: All your base are belong to us') >= 0
        self.is_leader = (became_leader or took_over)
        return self.is_leader

    def probe_leader(self):
        """ talk to the frontends to find out whether its a leader or not. """
        # Should this be moved to the AF script?
        self.is_leader = False
        for instance in self.get_frontends():
            if instance.probe_if_is_leader():
                self.is_leader = True
        return self.is_leader

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

class StarterNonManager(StarterManager):
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
            basecfg.index = 0;
        inst = ArangodRemoteInstance('coordinator',
                                     basecfg.frontends[basecfg.index].port,
                                     # self.cfg.localhost,
                                     basecfg.frontends[basecfg.index].ip,
                                     basecfg.frontends[basecfg.index].ip,
                                     Path('/'))
        self.all_instances.append(inst)
        basecfg.index += 1

    def run_starter(self):
        pass

    def detect_instances(self):
        self.detect_arangosh_instances()

    def detect_instance_pids(self):
        if not self.get_frontends():
            print("no frontends?")
            raise Exception("foobar")

    def is_instance_up(self):
        return True

    def detect_instance_pids(self):
        pass
