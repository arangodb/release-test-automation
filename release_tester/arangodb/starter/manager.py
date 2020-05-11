#!/usr/bin/env python
""" Manage one instance of the arangodb starter
    to crontroll multiple arangods
"""
import signal
import copy
import os
import time
import re
import logging
import subprocess
import sys
from pathlib import Path
import psutil
from tools.timestamp import timestamp
from arangodb.sh import ArangoshExecutor
# from tools.killall import sig_int_process
import tools.loghelper as lh

ON_WINDOWS = (sys.platform == 'win32')

class StarterManager():
    """ manage one starter instance"""
    def __init__(self,
                 basecfg,
                 install_prefix,
                 mode=None, port=None, jwtStr=None, moreopts=None):
        self.cfg = copy.deepcopy(basecfg)
        self.basedir = self.cfg.baseTestDir / install_prefix
        self.log_file = self.basedir / "arangodb.log"
        self.starter_port = port
        self.startupwait = 1
        self.username = 'root'
        self.passvoid = ''
        self.mode = mode
        self.is_master = None
        self.is_leader = False
        self.arangosh = None
        self.frontend_port = None
        self.all_instances = []
        self.executor = None
        self.moreopts = []
        self.instance = None
        self.sync_master_port = None
        self.agent_instance = None
        self.coordinator = None
        self.frontend_port = None
        self.db_instance = None
        self.expect_instance_count = 1
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
                    
        self.moreopts += moreopts
        self.jwtfile = Path()
        if jwtStr:
            self.basedir.mkdir(parents=True, exist_ok=True)
            self.jwtfile = self.basedir / 'jwt'
            self.jwtfile.write_text(jwtStr)
            self.moreopts = ['--auth.jwt-secret'
                             , str(self.jwtfile)] + self.moreopts
        if self.starter_port is not None:
            self.frontend_port = self.starter_port + 1
            self.moreopts += ["--starter.port", "%d" % self.starter_port]
        if self.cfg.verbose:
            self.moreopts += ["--log.verbose=true"]
        self.arguments = [
            "--log.console=false",
            "--log.file=true",
            "--starter.data-dir=%s" % self.basedir
        ] + self.moreopts

    def run_starter(self):
        """ launch the starter for this instance"""
        args = [
            self.cfg.bin_dir / 'arangodb'
        ] + self.arguments

        lh.log_cmd(args)
        self.instance = psutil.Popen(args)

        time.sleep(self.startupwait)
        logging.info("waited for: " + str(self.startupwait))

    def is_instance_running(self):
        """ check whether this is still running"""
        try:
            self.instance.wait(timeout=1)
        except:
            pass
        return self.instance.is_running()

    def is_instance_up(self):
        """ check whether all spawned arangods are fully bootet"""
        logging.info("checking if arangodb booted")
        if not self.instance.is_running():
            raise Exception(timestamp()
                            + "my instance is gone! "
                            + self.basedir)
        lfs = self.get_log_file()
        regx = re.compile(r'(\w*) up and running ')
        for line in lfs.splitlines():
            match = regx.search(line)
            if match is None:
                continue
            groups = match.groups()
            if len(groups) == 1 and groups[0] == 'agent':
                continue
            return True
        return False

    def terminate_instance(self):
        """ terminate the instance of this starter
            (it should kill all its managed services)"""
        logging.info("StarterManager: Terminating: %s", str(self.arguments))
        self.instance.terminate()
        logging.info("StarterManager: waiting for process to exit")
        self.instance.wait()
        logging.info("StarterManager: done - moving logfile from %s to %s",
                     str(self.log_file),
                     str(self.basedir / "arangodb.log.old"))
        self.log_file.rename(self.basedir / "arangodb.log.old")
        for instance in self.all_instances:
            logging.info("renaming instance logfile: %s -> %s",
                         instance['logfile'],
                         str(instance['logfile']) + '.old')
            instance['logfile'].rename(str(instance['logfile']) + '.old')

    def kill_instance(self):
        """ kill the instance of this starter
            (it won't kill its managed services)"""
        logging.info("StarterManager: Killing: %s", str(self.arguments))
        self.instance.send_signal(signal.SIGKILL)
        try:
            logging.info(str(self.instance.wait(timeout=45)))
        except:
            logging.info("StarterManager: timeout, doing hard kill.")
            self.instance.kill()
        logging.info("StarterManager: Instance now dead.")

    def replace_binary_for_upgrade(self, newInstallCfg):
        """ replace the parts of the installation with information after an upgrade"""

        """ On windows the install prefix may change, since we can't overwrite open files: """
        self.cfg.installPrefix = newInstallCfg.installPrefix
        logging.info("StarterManager: Killing my instance [%s]", str(self.instance.pid))
        self.kill_instance()
        self.detect_instance_pids_still_alive()
        self.respawn_instance()
        logging.info("StarterManager: respawned instance as [%s]", str(self.instance.pid))

    def command_upgrade(self):
        """ we will launch another starter, to tell the bunch to run the upgrade"""
        args = [
            self.cfg.bin_dir / 'arangodb',
            'upgrade',
            '--starter.endpoint',
            'http://127.0.0.1:' + str(self.get_my_port())
        ]
        logging.info("StarterManager: Commanding upgrade %s", str(args))
        self.upgradeprocess = psutil.Popen(args)

    def wait_for_upgrade(self):
        rc = self.upgradeprocess.wait()
        logging.info("StarterManager: Upgrade command exited: %s", str(rc))
        if rc != 0:
            raise Exception("Upgrade process exited with non-zero reply")

    def respawn_instance(self):
        """ restart the starter instance after we killed it eventually """
        args = [
            self.cfg.bin_dir / 'arangodb'
        ] + self.arguments

        logging.info("StarterManager: respawning instance %s", str(args))
        self.instance = psutil.Popen(args)
        time.sleep(self.startupwait)

    def execute_frontend(self, cmd):
        """ use arangosh to run a command on the frontend arangod"""
        return self.arangosh.run_command(cmd)

    def get_frontend_port(self):
        """ get the port of the arangod which is coordinator etc."""
        if self.frontend_port is None:
            raise Exception(timestamp() + "no frontend port detected")
        return self.frontend_port

    def get_my_port(self):
        if self.starter_port != None:
            return self.starter_port
        where = -1
        while where == -1:
            lf = self.get_log_file()
            where = lf.find('ArangoDB Starter listening on')
            if where != -1:
                where = lf.find(':', where)
                if where != -1:
                    end = lf.find(' ', where)
                    port = lf[where + 1: end]
                    self.starter_port = port
                    return port
            logging.info('&')
            time.sleep(1)

    def get_sync_master_port(self):
        """ get the port of a syncmaster arangosync"""
        self.sync_master_port = None
        pos = None
        sm_port_text = 'Starting syncmaster on port'
        sw_text = 'syncworker up and running'
        worker_count = 0
        while worker_count < 3 and self.is_instance_running():
            logging.info('%')
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

    def read_instance_logfile(self):
        """ get the logfile of the dbserver instance"""
        return self.db_instance['logfile'].read_text()

    def read_agent_logfile(self):
        """ get the agent logfile of this instance"""
        return self.agent_instance['logfile'].read_text()

    def detect_logfiles(self):
        """ see which arangods where spawned and inspect their logfiles"""

        logging.info("waiting for frontend")

        frontend_instance = None
        logfiles=set()
        tries = 10 * self.expect_instance_count # the more instances we expect to spawn the more patient.
        print('z'*80 + str(self.expect_instance_count))
        # wait for all instances to become alive. The last instance spawned is a frontend instance.
        
        while not frontend_instance and tries:
            self.all_instances = []
            sys.stdout.write(".")
            sys.stdout.flush()
            for root, dirs, files in os.walk(self.basedir):
                # logging.debug("iterating over:" + root)

                for f in files:
                    if f.endswith("log"):
                        logfiles.add(str(Path(root) / f))

                for name in dirs:
                    match = re.match(r'(agent|coordinator|dbserver|resilientsingle|single)(\d*)', name)
                    if match:
                        logfile =  self.basedir / name / 'arangod.log'
                        instance = {
                            'type': match.group(1),
                            'port': match.group(2),
                            'logfile': logfile
                        }

                        logging.info("found instance: " + instance["type"] + instance["port"])

                        if not logfile.exists():
                            logging.error("missing logfile: " + str(logfile))
                            raise RuntimeError("missing logfile")

                        if instance['type'] == 'coordinator':
                            self.all_instances.append(instance)
                            self.coordinator = instance
                            frontend_instance = instance
                            self.frontend_port = instance['port']
                        elif instance['type'] == 'resilientsingle':
                            self.all_instances.append(instance)
                            self.db_instance = instance
                            frontend_instance = instance
                            self.frontend_port = instance['port']
                        elif instance['type'] == 'single':
                            self.all_instances.append(instance)
                            self.db_instance = instance
                            frontend_instance = instance
                            self.frontend_port = instance['port']
                        # these are not frontend instances:
                        elif instance['type'] == 'agent':
                            self.all_instances.append(instance)
                            self.agent_instance = instance
                        elif instance['type'] == 'dbserver':
                            self.all_instances.append(instance)
                            self.db_instance = instance
                        else:
                            # logging.debug("directory not relevant:" + name)
                            pass


            else:
                tries -= 1
                if self.all_instances:
                    logging.debug("found instances: ")
                    for i in self.all_instances:
                        logging.debug(str(i))
                    logging.debug("-" * 80)

                time.sleep(5)

        if not frontend_instance:
            logging.error("can not continue without frontend instance")
            logging.error("please check logs in" + str(self.basedir))
            for x in logfiles:
                logging.debug(x)
            sys.exit(1)

        logging.info("waiting for frontend")
        while not frontend_instance['logfile'].exists():
            logging.info(">")
            time.sleep(1)
        logging.info("%s", str(self.all_instances))

    def detect_instance_pids(self):
        """ detect the arangod instance PIDs"""
        for instance in self.all_instances:
            instance['PID'] = 0
            while instance['PID'] == 0:
                lfs = instance['logfile'].read_text()
                pos = lfs.find('is ready for business.')
                if pos < 0:
                    logging.info(',')
                    time.sleep(1)
                    continue
                pos = lfs.rfind('\n', 0, pos)
                epos = lfs.find('\n', pos + 1, len(lfs))
                line = lfs[pos: epos]
                match = re.search(r'Z \[(\d*)\]', line)
                if match is None:
                    raise Exception(timestamp()
                                    + " Couldn't find a PID in hello line! - "
                                    + line)
                instance['PID'] = int(match.groups()[0])
        logging.info("StarterManager: detected instances: %s", str(self.all_instances))
        if self.arangosh is None:
            self.cfg.port = self.get_frontend_port()
            self.arangosh = ArangoshExecutor(self.cfg)

    def detect_instance_pids_still_alive(self):
        """ detecting whether the processes the starter spawned are still there """
        missing_instances = []
        running_pids = psutil.pids()
        for instance in self.all_instances:
            if instance['PID'] not in running_pids:
                missing_instances += [instance]
        if len(missing_instances) > 0:
            logging.info("not all instances are alive: %s", str(missing_instances))
            raise Exception("instances missing: " + str(missing_instances))
        else:
            logging.info("All arangod instances still found: %s", str(self.all_instances))

    def detect_leader(self):
        """ in active failover detect whether we run the leader"""
        lfs = self.read_instance_logfile()
        self.is_leader = (
            (lfs.find('Became leader in') >= 0) or
            (lfs.find('Successful leadership takeover:'
                      ' All your base are belong to us')
             >= 0))
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
