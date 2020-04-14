#!/usr/bin/env python
""" analyse the logfile of a running arangod instance
    for certain status messages """

import re
import time
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class ArangodLogExaminer():
    """ examine the logfiles of all arangods attached to one starter"""
    def __init__(self, config):
        self.cfg = config
        self.is_master = False
        self.is_leader = False
        self.frontend_port = 8529

    def detect_instance_pids(self):
        """ try to detect the PID of the current instances
            and check that they ready for business"""
        for i in self.cfg.all_instances:
            instance = self.cfg.all_instances[i]
            print(instance)
            instance['PID'] = 0
            while instance['PID'] == 0:
                lfh = open(instance['logfile'])
                last_line = ''
                lfc = ''
                for line in lfh:
                    if line == "":
                        continue
                    last_line = line
                    lfc += '\n' + line
                # print(last_line)
                match = re.search(r'Z \[(\d*)\]', last_line)
                if match is None:
                    logging.info("no PID in: %s", last_line)
                    continue
                pid = match.groups()[0]
                start = lfc.find(pid)
                pos = lfc.find('is ready for business.', start)
                if pos < 0:
                    logging.info('.')
                    time.sleep(1)
                    continue
                instance['PID'] = int(pid)
        logging.info(str(self.cfg.all_instances))

#   def detect_leader(self):
#       """ detect whether this instance is now an active failover leader"""
#       lfc = self.readInstanceLogfile()
#       self.is_leader = (
#           (lfc.find('Became leader in') >= 0) or
#           (lfc.find(
#               'Successful leadership takeover: All your base are belong to us')
#            >= 0))
#       return self.is_leader
#
#   def read_instance_logfile(self):
#       """fetch the log file into ram from a dbserver instance"""
#       return open(self.dbInstance['logfile']).read()
#
#   def read_agent_logfile(self):
#       """read agent logfiles"""
#       return open(self.agent['logfile']).read()
#
#   def active_failover_detect_hosts(self):
#       """detect which active failover instance is the leader"""
#       if not self.instance.is_running():
#           print(self.instance)
#           raise Exception(timestamp() + "my instance is gone! " + self.basedir)
#       # this is the way to detect the master starter...
#       lfc = self.getLogFile()
#       if lfc.find('Just became master') >= 0:
#           self.is_master = True
#       else:
#           self.is_master = False
#       regx = re.compile(r'Starting resilientsingle on port (\d*) .*')
#       match = regx.search(lfc)
#       if match is None:
#           print(regx)
#           print(match)
#           raise Exception(timestamp()
#                           + "Unable to get my host state! "
#                           + self.basedir
#                           + " - "
#                           + lfc)
#       self.frontend_port = match.groups()[0]
#
#   def active_failover_detect_host_now_follower(self):
#       """check whether a relaunched instance has now become a follower"""
#       if not self.instance.is_running():
#           raise Exception(timestamp() + "my instance is gone! " + self.basedir)
#       lfc = self.getLogFile()
#       if lfc.find('resilientsingle up and running as follower') >= 0:
#           self.is_master = False
#           return True
#       return False
