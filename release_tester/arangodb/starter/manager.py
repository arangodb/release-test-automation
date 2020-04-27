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
from pathlib import Path
import psutil
from tools.timestamp import timestamp
from arangodb.sh import ArangoshExecutor
from tools.killall import sig_int_process

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


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
        if self.mode:
            self.moreopts += ["--starter.mode", self.mode]
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
        self.arguments = [
            self.cfg.installPrefix / 'usr' / 'bin' / 'arangodb',
            "--log.console=false",
            "--log.file=true",
            "--starter.data-dir=%s" % self.basedir
        ] + self.moreopts

    def run_starter(self):
        """ launch the starter for this instance"""
        logging.info("launching %s", str(self.arguments))
        self.instance = psutil.Popen(self.arguments)
        time.sleep(self.startupwait)

    def is_instance_running(self):
        """ check whether this is still running"""
        try:
            self.instance.wait(timeout=1)
        except:
            pass
        return self.instance.is_running()

    def is_instance_up(self):
        """ check whether all spawned arangods are fully bootet"""
        if not self.instance.is_running():
            print(self.instance)
            print(self.instance.status())
            print(dir(self.instance))
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

    def kill_instance(self):
        """ kill the instance of this starter
            (it should kill all its managed services)"""
        logging.info("Killing: %s", str(self.arguments))
        sig_int_process(self.instance)
        
        #try: 
        #    self.instance.send_signal(signal.CTRL_C_EVENT)
        #except Exception as x:
        #    print(x)
        #    print(type(x))
        #    raise x
        #    # self.instance.terminate()
        #
        #print("xx"*80)
        #try:
        #    print("z"*80)
        #    self.wait(pid, timeout=45)
        #          
        #    print("y"*80)
        #except Exception as x:
        #    print("xxxxx")
        #    print(x)
        #    print(type(x))
        #    logging.info("timeout, doing hard kill.")
        #    self.instance.kill()
        #logging.info("Instance now dead.")

    def respawn_instance(self):
        """ restart the starter instance after we killed it eventually """
        logging.info("respawning instance %s", str(self.arguments))
        self.instance = psutil.Popen(self.arguments)
        time.sleep(self.startupwait)

    def execute_frontend(self, cmd):
        """ use arangosh to run a command on the frontend arangod"""
        if self.arangosh is None:
            self.cfg.port = self.get_frontend_port()
            self.arangosh = ArangoshExecutor(self.cfg)
        return self.arangosh.run_command(cmd)

    def get_frontend_port(self):
        """ get the port of the arangod which is coordinator etc."""
        if self.frontend_port is None:
            raise Exception(timestamp() + "no frontend port detected")
        return self.frontend_port

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
        for one in os.listdir(self.basedir):
            if os.path.isdir(os.path.join(self.basedir, one)):
                match = re.match(r'([a-z]*)(\d*)', one)
                instance = {
                    'type': match.group(1),
                    'port': match.group(2),
                    'logfile': self.basedir / one / 'arangod.log'
                    }
                if instance['type'] == 'agent':
                    self.agent_instance = instance
                elif instance['type'] == 'coordinator':
                    self.coordinator = instance
                    self.frontend_port = instance['port']
                elif instance['type'] == 'resilientsingle':
                    self.db_instance = instance
                    self.frontend_port = instance['port']
                else:
                    self.db_instance = instance
                self.all_instances.append(instance)
        logging.info("%s", str(self.all_instances))

    def detect_instance_pids(self):
        """ detect the arangod instance PIDs"""
        for instance in self.all_instances:
            instance['PID'] = 0
            while instance['PID'] == 0:
                lfs = self.db_instance['logfile'].read_text()
                pos = lfs.find('is ready for business.')
                if pos < 0:
                    logging.info('.')
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
        logging.info(str(self.all_instances))

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
            print(self.instance)
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
            print(regx)
            print(match)
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
