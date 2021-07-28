#!/usr/bin/env python
""" Manage one instance of the arangodb starter
    to crontroll multiple arangods
"""
import copy
import logging
import subprocess
from threading import Timer

import psutil
import semver

from tools.asciiprint import ascii_convert

from arangodb.async_client import (
    ArangoCLIprogressiveTimeoutExecutor,
    dummy_line_result
    )

class SyncManager(ArangoCLIprogressiveTimeoutExecutor):
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
        super().__init__(basecfg, None)

    def run_syncer(self):
        """ launch the syncer for this instance """
        args = [
        ] + self.arguments

        return self. run_monitored(self.cfg.bin_dir / 'arangosync',
                                   self.arguments,
                                   999,
                                   dummy_line_result,
                                   self.cfg.verbose)

    def replace_binary_for_upgrade(self, new_install_cfg):
        """ set the new config properties """
        self.cfg.installPrefix = new_install_cfg.installPrefix

    def check_sync_status(self, which):
        """ run the syncer status command """
        logging.info('SyncManager: Check status of cluster %s', str(which))
        args = [
            'get', 'status',
            '--master.cacert=' + str(self.certificate_auth["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[which])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"]),
            '--verbose']
        return self.run_monitored(self.cfg.bin_dir / 'arangosync',
                                  args,
                                  999,
                                  dummy_line_result,
                                  self.cfg.verbose)

    def get_sync_tasks(self, which):
        """ run the get tasks command """
        logging.info('SyncManager: Check tasks of cluster %s', str(which))
        args = [
            'get', 'tasks',
            '--master.cacert=' + str(self.certificate_auth["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[which])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"]),
            '--verbose']
        return self.run_monitored(self.cfg.bin_dir / 'arangosync',
                                  args,
                                  999,
                                  dummy_line_result,
                                  self.cfg.verbose)

    def stop_sync(self, timeout=60, more_args=[]):
        """ run the stop sync command """
        output = rb''
        err = rb''
        exitcode = 1
        args = [
            'stop', 'sync',
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[0])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"])
        ] + more_args
        logging.info('SyncManager: stopping sync : %s', str(args))
        # todo: do we need an absolute timeout?
        # instance = psutil.Popen(args,
        #                         stdout=subprocess.PIPE,
        #                         stderr=subprocess.PIPE)
        # timer = Timer(timeout, instance.kill)
        # try:
        #     timer.start()
        #     (output, err) = instance.communicate()
        # finally:
        #     timer.cancel()
        # exitcode = instance.wait()
        # return (ascii_convert(output),ascii_convert(err),  exitcode)
        return self.run_monitored(self.cfg.bin_dir / 'arangosync',
                                  args,
                                  timeout,
                                  dummy_line_result,
                                  self.cfg.verbose)

    def abort_sync(self):
        """ run the stop sync command """
        args = [
            'abort', 'sync',
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[0])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"])
        ]
        logging.info('SyncManager: stopping sync : %s', str(args))
        return self.run_monitored(self.cfg.bin_dir / 'arangosync',
                                  args,
                                  300,
                                  dummy_line_result,
                                  self.cfg.verbose)

    def check_sync(self):
        """ run the check sync command """
        if self.version < semver.VersionInfo.parse('1.0.0'):
            logging.warning('SyncManager: checking sync consistency :'
                            ' available since 1.0.0 of arangosync')
            return ("", "", True)

        args = [
            'check', 'sync',
            '--master.cacert=' + str(self.certificate_auth["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[0])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"])
        ]
        logging.info('SyncManager: checking sync consistency : %s', str(args))
        success, output, exit_code, dummy = self.run_monitored(
            self.cfg.bin_dir / 'arangosync',
            args,
            300,
            dummy_line_result,
            self.cfg.verbose)

        success = output.find('The whole data is the same') >= 0
        return (success, output)

    def reset_failed_shard(self, database, collection):
        """ run the check sync command """
        if self.version < semver.VersionInfo.parse('1.0.0'):
            logging.warning('SyncManager: checking sync consistency :'
                            ' available since 1.0.0 of arangosync')
            return True

        args = [
            'reset', 'failed', 'shard',
            '--master.cacert=' + str(self.certificate_auth["cert"]),
            '--master.endpoint=https://{url}:{port}'.format(
                url=self.cfg.publicip,
                port=str(self.clusterports[0])),
            '--auth.keyfile=' + str(self.certificate_auth["clientkeyfile"]),
            '--database', database, '--collection', collection
        ]
        logging.info('SyncManager: resetting failed shard : %s', str(args))
        success, output, exit_code, dummy = self.run_monitored(
            self.cfg.bin_dir / 'arangosync',
            args,
            300,
            dummy_line_result,
            self.cfg.verbose)
        return success
