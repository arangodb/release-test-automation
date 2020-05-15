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

from enum import Enum

class InstanceType(Enum):
    coordinator = 1
    resilientsingle = 2
    single = 3
    agent = 4
    dbserver = 5

class ArangodInstance():
    def __init__(self, typ, port):
        self.type = InstanceType[typ] # convert to enum
        self.port = port
        self.pid = None
        self.logfile = None
        self.name = self.type.name + str(self.port)
        logging.info("creating arango instance: {0.name}".format(self))

    def __repr__(self):
        return """
arangod
    name:    {0.name}
    pid:     {0.pid}
    logfile: {0.logfile}
""".format(self)

    def is_frontend(self):
        if self.type in [ InstanceType.coordinator
                        , InstanceType.resilientsingle
                        , InstanceType.single ]:
            return True
        else:
            return False

    def is_dbserver(self):
        if self.type in [ InstanceType.dbserver
                        , InstanceType.resilientsingle
                        , InstanceType.single ]:
            return True
        else:
            return False

class StarterManager():
    """ manages one starter instance"""
    def __init__(self,
                 basecfg,
                 install_prefix,
                 mode=None, port=None, jwtStr=None, moreopts=[]):

        self.moreopts = moreopts
        self.cfg = copy.deepcopy(basecfg)
        if self.cfg.verbose:
            self.moreopts += ["--log.verbose=true"]

        #directories
        self.name = str(install_prefix)
        self.basedir = self.cfg.baseTestDir / install_prefix
        self.log_file = self.basedir / "arangodb.log"

        #arg port - can be set - otherwise it is read from the log later
        self.starter_port = port
        if self.starter_port is not None:
            self.moreopts += ["--starter.port", "%d" % self.starter_port]

        # arg - jwtstr
        self.jwtfile = None
        if jwtStr:
            self.basedir.mkdir(parents=True, exist_ok=True)
            self.jwtfile = self.basedir / 'jwt'
            self.jwtfile.write_text(jwtStr)
            self.moreopts += ['--auth.jwt-secret' , str(self.jwtfile)]

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

        self.arguments = [
            "--log.console=false",
            "--log.file=true",
            "--starter.data-dir={0.basedir}".format(self)
        ] + self.moreopts

    def name(self):
        return str(self.name)

    def get_frontends(self):
        rv = [ ]
        for i in self.all_instances:
            if i.is_frontend():
                rv.append(i)
        return rv

    def get_dbservers(self):
        rv = [ ]
        for i in self.all_instances:
            if i.is_dbserver():
                rv.append(i)
        return rv

    def get_agents(self):
        rv = [ ]
        for i in self.all_instances:
            if i.type == InstanceType.agent:
                rv.append(i)
        return rv

    def get_frontend(self):
        servers = self.get_frontends()
        assert servers
        return servers[0]

    def get_dbserver(self):
        servers = self.get_dbservers()
        assert servers
        return servers[0]

    def get_agent(self):
        servers = self.get_agents()
        assert servers
        return servers[0]

    def show_all_instances(self):
        logging.info("arangod instances for starter: " + self.name)
        if not self.all_instances:
            logging.info("no instances detected")
            return

        logging.info("detected instances: ----")
        for instance in self.all_instances:
            print(" - " + instance.name)
        logging.info("------------------------")


    def run_starter(self):
        """ launch the starter for this instance"""
        logging.info("running starter " + self.name)
        args = [ self.cfg.bin_dir / 'arangodb' ] + self.arguments

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
        logging.info("checking if starter instance booted: " + str(self.basedir))
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
        lh.section("terminating instances")
        logging.info("StarterManager: Terminating starter instance: %s", str(self.arguments))
        self.instance.terminate()

        logging.info("StarterManager: waiting for process to exit")
        self.instance.wait()

        logging.info("StarterManager: done - moving logfile from %s to %s",
                     str(self.log_file),
                     str(self.basedir / "arangodb.log.old"))
        self.log_file.rename(self.basedir / "arangodb.log.old")
        for instance in self.all_instances:
            l = str(instance.logfile)
            logging.info("renaming instance logfile: %s -> %s", l, l + '.old')
            instance.logfile.rename(l + '.old')
        #FIXME DEAD instances must be removed from `self.all_instances`
        #      or at least the pid needs to be deleted. Ask dothebart for his
        #      resoning.

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
        #FIXME check / update pids and logfiles after respawn?
        #      Not required when restarting the starter only.
        #      When arangods are upgraded it becomes necessary

    def execute_frontend(self, cmd):
        """ use arangosh to run a command on the frontend arangod"""
        return self.arangosh.run_command(cmd)

    def get_frontend_port(self):
        """ get the port of the arangod which is coordinator etc."""
        #FIXME This looks unreliable to me, especially when terminating
        #      instances. How will the variable get updated?
        if self.frontend_port:
            return self.frontend_port
        return self.get_frontend().port

    def get_my_port(self):
        if self.starter_port != None:
            return self.starter_port

        where = -1
        tries = 10
        while where == -1 and tries:
            tries -= 1
            lf = self.get_log_file()
            where = lf.find('ArangoDB Starter listening on')
            if where != -1:
                where = lf.find(':', where)
                if where != -1:
                    end = lf.find(' ', where)
                    port = lf[where + 1: end]
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

    def detect_logfiles(self):
        """ see which arangods where spawned and inspect their logfiles"""
        lh.subsection("Instance Detection")
        logging.debug("waiting for frontend")
        logfiles=set() #logfiles that can be used for debugging

         # the more instances we expect to spawn the more patient:
        tries = 10 * self.expect_instance_count

        # Wait for forntend to become alive.
        while not self.get_frontends() and tries:
            self.all_instances = []
            sys.stdout.write(".")
            sys.stdout.flush()

            for root, dirs, files in os.walk(self.basedir):
                for f in files:
                    if f.endswith("log"):
                        logfiles.add(str(Path(root) / f))

                for name in dirs:
                    match = re.match(r'(agent|coordinator|dbserver|resilientsingle|single)(\d*)', name)
                    if match:
                        logfile = self.basedir / name / 'arangod.log'

                        if not logfile.exists():
                            #wait for logfile
                            continue

                        instance = ArangodInstance(match.group(1), match.group(2))
                        instance.logfile = logfile
                        self.all_instances.append(instance)

            if not self.get_frontends():
                tries -= 1
                time.sleep(5)

        if not self.get_frontends():
            logging.error("STARTER FAILED TO SPAWN ARANGOD")
            self.show_all_instances()
            logging.error("can not continue without frontend instance")
            logging.error("please check logs in" + str(self.basedir))
            for x in logfiles:
                logging.debug(x)
            sys.exit(1)

        self.show_all_instances()

    def detect_instance_pids(self):
        """ detect the arangod instance PIDs"""
        for instance in self.all_instances:
            while not instance.pid:
                lfs = instance.logfile.read_text()
                pos = lfs.find('is ready for business.')
                if pos < 0:
                    print('.')
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
                instance.pid = int(match.groups()[0])

        self.show_all_instances()
        if self.arangosh is None:
            self.cfg.port = self.get_frontend_port()
            self.arangosh = ArangoshExecutor(self.cfg)

    def detect_instance_pids_still_alive(self):
        """ detecting whether the processes the starter spawned are still there """
        missing_instances = []
        running_pids = psutil.pids()
        for instance in self.all_instances:
            if instance.pid not in running_pids:
                missing_instances.append(instance)

        if len(missing_instances) > 0:
            logging.error("Not all instances are alive. The following are not running: %s", str(missing_instances))
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
        self.is_leader = ( became_leader or took_over )
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

        #TODO FIX - fragile logic  - readd member for now
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
