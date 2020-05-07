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

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class SyncManager():
    """ manager arangosync instance """
    def __init__(self,
                 basecfg,
                 ca,
                 clusterports):
        self.cfg = copy.deepcopy(basecfg)
        self.ca = ca
        self.clusterports = clusterports
        self.arguments = ['configure', 'sync',
               '--master.endpoint=https://'
               + self.cfg.publicip
               + ':'
               + str(clusterports[0]),
               '--master.keyfile=' + str(self.ca["clientkeyfile"]),
               '--source.endpoint=https://'
               + self.cfg.publicip
               + ':'
               + str(clusterports[1]),
               '--master.cacert=' + str(self.ca["cert"]),
               '--source.cacert=' + str(self.ca["cert"]),
               '--auth.keyfile=' + str(self.ca["clientkeyfile"])]
        self.instance = None

    def run_syncer(self):
        """ launch the syncer for this instance """
        args = [
            self.cfg.bin_dir / 'arangosync'
        ] + self.arguments
        
        logging.info("SyncManager: launching %s", str(args))
        rc = psutil.Popen(args).wait()
        logging.info("SyncManager: up %s", str(rc))
        return rc == 0

    def is_instance_running(self):
        """ check whether this is still running"""
        try:
            self.instance.wait(timeout=1)
        except:
            pass
        return self.instance.is_running()

    def respawn_instance(self):
        """ restart the arangosync instance after we killed it eventually """
        args = [
            self.cfg.bin_dir / 'arangosync'
        ] + self.arguments
        
        logging.info("SyncManager: respawning instance %s", str(args))
        self.instance = psutil.Popen(args)
        logging.info("SyncManager: up %s", str(self.instance.pid))

    def terminate_instance(self):
        """ terminate the instance of this syncer"""
        logging.info("SyncManager: Terminating: %s", str(self.arguments))
        #self.instance.send_signal(signal.CTRL_C_EVENT)
        self.instance.terminate()
        try:
            logging.info(str(self.instance.wait(timeout=45)))
        except:
            logging.info("SyncManager: timeout, doing hard kill.")
            self.instance.kill()
        logging.info("SyncManager: Instance now dead.")

    def replace_binary_for_upgrade(self, newInstallCfg):
        self.cfg.installPrefix = newInstallCfg.installPrefix

    def check_sync_status(self, which):
        logging.info('SyncManager: Check status of cluster %s', str(which))
        args = [
            self.cfg.bin_dir / 'arangosync'
            'get', 'status',
            '--master.cacert=' + str(self.ca["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[which])),
            '--auth.keyfile=' + str(self.ca["clientkeyfile"]),
            '--verbose']
        logging.info(args)
        psutil.Popen(args).wait()

    def get_sync_tasks(self, which):
        logging.info('SyncManager: Check status of cluster %s', str(which))
        args = [
            self.cfg.bin_dir / 'arangosync'
            'get', 'tasks',
            '--master.cacert=' + str(self.ca["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[which])),
            '--auth.keyfile=' + str(self.ca["clientkeyfile"]),
            '--verbose']
        logging.info(args)
        psutil.Popen(args).wait()

    def stop_sync(self):
        args = [
            self.cfg.bin_dir / 'arangosync'
            'abort', 'sync',
            '--master.cacert=' + str(self.ca["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[0])),
            '--auth.keyfile=' + str(self.ca["clientkeyfile"])
        ]
        logging.info('SyncManager: stopping sync : %s', str(args))
        psutil.Popen(args).wait()
        
