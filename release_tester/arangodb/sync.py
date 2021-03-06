#!/usr/bin/env python
""" Manage one instance of the arangodb starter
    to crontroll multiple arangods
"""
import copy
import logging
import psutil

class SyncManager():
    """ manage arangosync """
    def __init__(self,
                 basecfg,
                 ca,
                 clusterports):
        self.cfg = copy.deepcopy(basecfg)
        self.ca = ca
        self.clusterports = clusterports
        self.arguments = [
            'configure', 'sync',
            '--master.endpoint=https://{ip}:{port}'.format(ip=self.cfg.publicip, port=str(clusterports[0])),
            '--master.keyfile=' + str(self.ca["clientkeyfile"]),
            '--source.endpoint=https://{ip}:{port}'.format(ip=self.cfg.publicip, port=str(clusterports[1])),
            '--master.cacert=' + str(self.ca["cert"]),
            '--source.cacert=' + str(self.ca["cert"]),
            '--auth.keyfile=' + str(self.ca["clientkeyfile"])
        ]

        self.instance = None

    def run_syncer(self):
        """ launch the syncer for this instance """
        args = [
            self.cfg.bin_dir / 'arangosync',
        ] + self.arguments

        logging.info("SyncManager: launching %s", str(args))
        exitcode = psutil.Popen(args).wait()
        logging.info("SyncManager: up %s", str(exitcode))
        return exitcode == 0

    def replace_binary_for_upgrade(self, new_install_cfg):
        """ set the new config properties """
        self.cfg.installPrefix = new_install_cfg.installPrefix

    def check_sync_status(self, which):
        """ run the syncer status command """
        logging.info('SyncManager: Check status of cluster %s', str(which))
        args = [
            self.cfg.bin_dir / 'arangosync',
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
        """ run the get tasks command """
        logging.info('SyncManager: Check status of cluster %s', str(which))
        args = [
            self.cfg.bin_dir / 'arangosync',
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
        """ run the stop sync command """
        args = [
            self.cfg.bin_dir / 'arangosync',
            'abort', 'sync',
            '--master.cacert=' + str(self.ca["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[0])),
            '--auth.keyfile=' + str(self.ca["clientkeyfile"])
        ]
        logging.info('SyncManager: stopping sync : %s', str(args))
        psutil.Popen(args).wait()

    def check_sync(self):
        """ run the stop sync command """
        args = [
            self.cfg.bin_dir / 'arangosync',
            'check', 'sync',
            '--master.cacert=' + str(self.ca["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[0])),
            '--auth.keyfile=' + str(self.ca["clientkeyfile"])
        ]
        logging.info('SyncManager: checking sync status : %s', str(args))
        return psutil.Popen(args).wait() == 0
        
