#!/usr/bin/env python
""" Manage one instance of the arangodb starter
    to crontroll multiple arangods
"""
import copy
import logging
import subprocess

import psutil
import semver

from tools.asciiprint import ascii_convert

class SyncManager():
    """ manage arangosync """
    def __init__(self,
                 basecfg,
                 certificate_auth,
                 clusterports,
                 version):
        self.cfg = copy.deepcopy(basecfg)
        self.certificate_auth = certificate_auth
        self.clusterports = clusterports
        self.arguments = [
            'configure', 'sync',
            '--master.endpoint=https://{ip}:{port}'.format(
                ip=self.cfg.publicip,
                port=str(clusterports[0])),
            '--master.keyfile=' + str(self.certificate_auth["clientkeyfile"]),
            '--source.endpoint=https://{ip}:{port}'.format(
                ip=self.cfg.publicip,
                port=str(clusterports[1])),
            '--master.cacert=' + str(self.certificate_auth["cert"]),
            '--source.cacert=' + str(self.certificate_auth["cert"]),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"])
        ]
        self.version = version
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
            '--master.cacert=' + str(self.certificate_auth["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[which])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"]),
            '--verbose']
        logging.info(args)
        psutil.Popen(args).wait()

    def get_sync_tasks(self, which):
        """ run the get tasks command """
        logging.info('SyncManager: Check tasks of cluster %s', str(which))
        args = [
            self.cfg.bin_dir / 'arangosync',
            'get', 'tasks',
            '--master.cacert=' + str(self.certificate_auth["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[which])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"]),
            '--verbose']
        logging.info(args)
        psutil.Popen(args).wait()

    def stop_sync(self):
        """ run the stop sync command """
        args = [
            self.cfg.bin_dir / 'arangosync',
            'stop', 'sync',
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[0])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"])
        ]
        logging.info('SyncManager: stopping sync : %s', str(args))
        psutil.Popen(args).wait(60)

    def abort_sync(self):
        """ run the stop sync command """
        args = [
            self.cfg.bin_dir / 'arangosync',
            'abort', 'sync',
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[0])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"])
        ]
        logging.info('SyncManager: stopping sync : %s', str(args))
        psutil.Popen(args).wait()

    def check_sync(self):
        """ run the check sync command """
        if self.version < semver.VersionInfo.parse('1.0.0'):
            logging.warning('SyncManager: checking sync consistency :'
                            ' available since 1.0.0 of arangosync')
            return ("", "", True)

        args = [
            self.cfg.bin_dir / 'arangosync',
            'check', 'sync',
            '--master.cacert=' + str(self.certificate_auth["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[0])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"])
        ]
        logging.info('SyncManager: checking sync consistency : %s', str(args))
        instance = psutil.Popen(args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (output, err) = instance.communicate()
        instance.wait()
        output = ascii_convert(output)
        print(output)
        success = output.find('The whole data is the same') >= 0
        return (output, ascii_convert(err), success)


    def reset_failed_shard(self, database, collection):
        """ run the check sync command """
        if self.version < semver.VersionInfo.parse('1.0.0'):
            logging.warning('SyncManager: checking sync consistency :'
                            ' available since 1.0.0 of arangosync')
            return True

        args = [
            self.cfg.bin_dir / 'arangosync',
            'reset', 'failed', 'shard',
            '--master.cacert=' + str(self.certificate_auth["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[0])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"]),
            '--database', database, '--collection', collection
        ]
        logging.info('SyncManager: resetting failed shard : %s', str(args))
        return psutil.Popen(args).wait() == 0
