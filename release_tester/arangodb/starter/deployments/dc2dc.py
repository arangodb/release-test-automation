#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path
import re

import psutil
import requests
import semver
from arangodb.starter.manager import StarterManager
from arangodb.sync import SyncManager
from arangodb.starter.deployments.runner import Runner, PunnerProperties
from arangodb.instance import InstanceType
from tools.asciiprint import print_progress as progress

VERSION_OLD_MIN_FIX = semver.VersionInfo.parse('1.5.0')
VERSION_OLD_MAX_FIX = semver.VersionInfo.parse('2.0.0')
VERSION_NEW_FIX = semver.VersionInfo.parse('2.3.0')
USERS_ERROR_RX = re.compile('.*\n.*\n.*(_users).*DIFFERENT.*', re.MULTILINE)

class Dc2Dc(Runner):
    """ this launches two clusters in dc2dc mode """
    # pylint: disable=R0913 disable=R0902
    def __init__(self, runner_type, abort_on_error, installer_set,
                 selenium, selenium_driver_args,
                 testrun_name: str):
        super().__init__(runner_type, abort_on_error, installer_set,
                         PunnerProperties('DC2DC', 0, 3500, True),
                         selenium, selenium_driver_args,
                         testrun_name)
        self.success = True
        self.cfg.passvoid = ''
        self.sync_manager = None
        self.sync_version = None
        self.cluster1 = {}
        self.cluster2 = {}
        self.certificate_auth = {}
        self.source_dc = None
        # self.hot_backup = False

    def starter_prepare_env_impl(self):
        def cert_op(args):
            print(args)
            psutil.Popen([self.cfg.bin_dir / 'arangodb',
                          'create'] +
                         args).wait()
        datadir = Path('data')
        cert_dir = self.cfg.base_test_dir / self.basedir / "certs"
        print(cert_dir)
        cert_dir.mkdir(parents=True, exist_ok=True)
        cert_dir.mkdir(parents=True, exist_ok=True)
        def getdirs(subdir):
            return {
                "dir": self.basedir /
                       self.cfg.base_test_dir /
                       self.basedir / datadir,
                "instance_dir": subdir,
                "SyncSecret": cert_dir / subdir / 'syncmaster.jwtsecret',
                "JWTSecret": cert_dir / subdir / 'arangodb.jwtsecret',
                "tlsKeyfile": cert_dir / subdir / 'tls.keyfile',
            }

        self.cluster1 = getdirs(Path('cluster1'))
        self.cluster2 = getdirs(Path('cluster2'))
        client_cert = cert_dir / 'client-auth-ca.crt'
        self.certificate_auth = {
            "cert": cert_dir / 'tls-ca.crt',
            "key": cert_dir / 'tls-ca.key',
            "clientauth_key": cert_dir / 'client-auth-ca.key',
            "clientkeyfile": cert_dir / 'client-auth-ca.keyfile'
        }
        logging.info('Create TLS certificates')
        cert_op(['tls', 'ca',
                 '--cert=' + str(self.certificate_auth["cert"]),
                 '--key=' + str(self.certificate_auth["key"])])
        cert_op(['tls', 'keyfile',
                 '--cacert=' + str(self.certificate_auth["cert"]),
                 '--cakey=' + str(self.certificate_auth["key"]),
                 '--keyfile=' + str(self.cluster1["tlsKeyfile"]),
                 '--host=' + self.cfg.publicip, '--host=localhost'])
        cert_op(['tls', 'keyfile',
                 '--cacert=' + str(self.certificate_auth["cert"]),
                 '--cakey=' + str(self.certificate_auth["key"]),
                 '--keyfile=' + str(self.cluster2["tlsKeyfile"]),
                 '--host=' + self.cfg.publicip, '--host=localhost'])
        logging.info('Create client authentication certificates')
        cert_op(['client-auth', 'ca',
                 '--cert=' + str(client_cert),
                 '--key=' + str(self.certificate_auth["clientauth_key"])])
        cert_op(['client-auth', 'keyfile',
                 '--cacert=' + str(client_cert),
                 '--cakey=' + str(self.certificate_auth["clientauth_key"]),
                 '--keyfile=' + str(self.certificate_auth["clientkeyfile"])])
        logging.info('Create JWT secrets')
        for node in [self.cluster1, self.cluster2]:
            cert_op(['jwt-secret', '--secret=' + str(node["SyncSecret"])])
            cert_op(['jwt-secret', '--secret=' + str(node["JWTSecret"])])

        def add_starter(val, port):
            val["instance"] = StarterManager(
                self.cfg,
                val["dir"], val["instance_dir"],
                port=port,
                mode='cluster',
                expect_instances=[
                    InstanceType.AGENT,
                    InstanceType.AGENT,
                    InstanceType.AGENT,
                    InstanceType.COORDINATOR,
                    InstanceType.COORDINATOR,
                    InstanceType.COORDINATOR,
                    InstanceType.DBSERVER,
                    InstanceType.DBSERVER,
                    InstanceType.DBSERVER,
                    InstanceType.SYNCMASTER,
                    InstanceType.SYNCMASTER,
                    InstanceType.SYNCMASTER,
                    InstanceType.SYNCWORKER,
                    InstanceType.SYNCWORKER,
                    InstanceType.SYNCWORKER
                ],
                moreopts=[
                    '--all.log.level=backup=trace',
                    '--all.log.level=requests=debug',
                    '--starter.sync',
                    '--starter.local',
                    '--auth.jwt-secret=' +           str(val["JWTSecret"]),
                    '--sync.server.keyfile=' +       str(val["tlsKeyfile"]),
                    '--sync.server.client-cafile=' + str(client_cert),
                    '--sync.master.jwt-secret=' +    str(val["SyncSecret"]),
                    '--starter.address=' +           self.cfg.publicip
                ])
            val["instance"].set_jwt_file(val["JWTSecret"])
            if port is None:
                val["instance"].is_leader = True

        add_starter(self.cluster1, None)
        add_starter(self.cluster2, port=9528)
        self.starter_instances = [self.cluster1['instance'],
                                  self.cluster2['instance']]

    def starter_run_impl(self):
        def launch(cluster):
            inst = cluster["instance"]
            inst.run_starter()
            while not inst.is_instance_up():
                logging.info('.')
                time.sleep(1)
            inst.detect_instances()
            inst.detect_instance_pids()
            cluster['smport'] = inst.get_sync_master_port()

            url = 'http://{host}:{port}'.format(
                host=self.cfg.publicip,
                port=str(cluster['smport']))
            reply = requests.get(url)
            logging.info(str(reply))
            logging.info(str(reply.raw))

        launch(self.cluster1)
        launch(self.cluster2)

    def _launch_sync(self, direction):
        """ configure / start a sync """
        from_to_dc = None
        if direction:
            from_to_dc = [self.cluster2['smport'],
                          self.cluster1['smport']]
            self.source_dc = from_to_dc[0]
        else:
            from_to_dc = [self.cluster1['smport'],
                          self.cluster2['smport']]
            self.source_dc = from_to_dc[1]
        self.sync_manager = SyncManager(self.cfg,
                                        self.certificate_auth,
                                        from_to_dc,
                                        self.sync_version)
        if not self.sync_manager.run_syncer():
            raise Exception("starting the synchronisation failed!")

    def finish_setup_impl(self):
        self.sync_version = self._get_sync_version()
        self._launch_sync(True)

        self.makedata_instances = [ self.cluster1['instance'] ]
        self.set_frontend_instances()
        count = 0
        for node in self.starter_instances:
            node.set_passvoid('dc2dc', count == 0)
            count += 1
        self.passvoid = 'dc2dc'

    def _get_sync_version(self):
        """
        Check version of the arangosync master on the first cluster
        """
        cluster_instance = self.cluster1['instance']

        token = cluster_instance.get_jwt_token_from_secret_file(self.cluster1["SyncSecret"])
        url = cluster_instance.get_sync_master().get_public_plain_url()
        url = 'https://' + url + '/_api/version'
        response = requests.get(url,
                                headers={'Authorization': 'Bearer ' + token},
                                verify=False)

        if response.status_code != 200:
            raise Exception("could not fetch arangosync version from {0}".format(url))

        version = response.json().get('version')
        if not version:
            raise Exception("missing version in reponse from {0}".format(url))
        print("Arangosync v%s detected" % version)
        return semver.VersionInfo.parse(version)

    def _stop_sync(self, timeout=60):
        output = None
        err = None
        for count in range (10):
            try:
                self.sync_manager.stop_sync(timeout)
                break
            except psutil.TimeoutExpired as ex:
                print("stopping didn't work out in time, force killing! " + str(ex))
                self.cluster1["instance"].kill_sync_processes()
                self.cluster2["instance"].kill_sync_processes()
                time.sleep(3)
                self.cluster1["instance"].detect_instances()
                self.cluster2["instance"].detect_instances()
        else:
            self.state += "\n" + output
            self.state += "\n" + err
            raise Exception("failed to stop the synchronisation in 10 attempts")

    def _mitigate_known_issues(self, last_sync_output):
        """
        this function contains counter measures against known issues of arangosync
        """
        if re.match(USERS_ERROR_RX, last_sync_output):
            self.progress(True, 'arangosync: resetting users collection...')
            self.sync_manager.reset_failed_shard('_system', '_users')
        elif last_sync_output.find(
                'temporary failure with http status code: 503: service unavailable') >= 0:
            if (self.sync_version < VERSION_OLD_MIN_FIX or (
                    (self.sync_version >= VERSION_OLD_MAX_FIX) and
                    (self.sync_version < VERSION_NEW_FIX))):
                self.progress(True, 'arangosync: restarting instances...')
                self.cluster1["instance"].kill_sync_processes()
                self.cluster2["instance"].kill_sync_processes()
                time.sleep(3)
                self.cluster1["instance"].detect_instances()
                self.cluster2["instance"].detect_instances()
            else:
                self.progress(
                    True,
                    'arangosync: {0} does not qualify for restart workaround..'.format(
                    str(self.sync_version))
                )
        elif last_sync_output.find('Shard is not turned on for synchronizing') >= 0:
            self.progress(True, 'arangosync: sync in progress.')
        else:
            self.progress(True, 'arangosync: unknown error condition, doing nothing.')

    def _get_in_sync(self, attempts):
        self.progress(True, "waiting for the DCs to get in sync")
        output = None
        err = None
        for count in range (attempts):
            (output, err, result) = self.sync_manager.check_sync()
            if result:
                print("CHECK SYNC OK!")
                break
            progress("sx" + str(count))
            self._mitigate_known_issues(output)
            time.sleep(10)
        else:
            self.state += "\n" + output
            self.state += "\n" + err
            raise Exception("failed to get the sync status")

    def test_setup_impl(self):
        self.cluster1['instance'].arangosh.check_test_data("dc2dc (post setup - dc1)")
        self._get_in_sync(20)

        res = self.cluster2['instance'].arangosh.check_test_data("dc2dc (post setup - dc2)")
        if not res[0]:
            if not self.cfg.verbose:
                print(res[1])
            raise Exception("error during verifying of "
                            "the test data on the target cluster")
        res = self.cluster1['instance'].arangosh.run_in_arangosh(
            (
                self.cfg.test_data_dir /
                Path('tests/js/server/replication/fuzz/replication-fuzz-global.js')
            ),
            [],
            [self.cluster2['instance'].get_frontend().get_public_url(
                'root:%s@'%self.passvoid)]
            )
        if not res[0]:
            if not self.cfg.verbose:
                print(res[1])
            raise Exception("replication fuzzing test failed")
        self._get_in_sync(12)

    def wait_for_restore_impl(self, backup_starter):
        for dbserver in self.cluster1["instance"].get_dbservers():
            dbserver.detect_restore_restart()

    def upgrade_arangod_version_impl(self):
        """ upgrade this installation """
        self._stop_sync()
        self.sync_manager.replace_binary_for_upgrade(self.new_cfg)
        self.cluster1["instance"].replace_binary_for_upgrade(self.new_cfg)
        self.cluster2["instance"].replace_binary_for_upgrade(self.new_cfg)
        self.cluster1["instance"].command_upgrade()
        self.cluster2["instance"].command_upgrade()

        # workaround: kill the sync'ers by hand, the starter doesn't
        # self._stop_sync()
        self.cluster1["instance"].kill_sync_processes()
        self.cluster2["instance"].kill_sync_processes()

        self.cluster1["instance"].wait_for_upgrade(300)
        self.cluster2["instance"].wait_for_upgrade(300)

        # self.sync_manager.start_sync()

        self.cluster1["instance"].detect_instances()
        self.cluster2["instance"].detect_instances()
        self.sync_manager.run_syncer()

        self.sync_version = self._get_sync_version()
        self.sync_manager.check_sync_status(0)
        self.sync_manager.check_sync_status(1)
        self.sync_manager.get_sync_tasks(0)
        self.sync_manager.get_sync_tasks(1)

    def jam_attempt_impl(self):
        """ stress the DC2DC, test edge cases """
        self.progress(True, "stopping sync")
        self._stop_sync()
        self.progress(True, "creating volatile data on secondary DC")
        self.cluster2["instance"].arangosh.hotbackup_create_nonbackup_data()
        self.progress(True, "restarting sync")
        self._launch_sync(True)
        self._get_in_sync(20)

        self.progress(True, "checking whether volatile data has been removed from both DCs")
        if (not self.cluster1["instance"].arangosh.hotbackup_check_for_nonbackup_data() or
            not self.cluster2["instance"].arangosh.hotbackup_check_for_nonbackup_data()):
            raise Exception("expected data created on disconnected follower DC to be gone!")

        self.progress(True, "stopping sync")
        self._stop_sync(120)
        self.progress(True, "reversing sync direction")
        self._launch_sync(False)
        self._get_in_sync(20)

    def shutdown_impl(self):
        self.cluster1["instance"].terminate_instance()
        self.cluster2["instance"].terminate_instance()

    def before_backup_impl(self):
        self.sync_manager.abort_sync()

    def after_backup_impl(self):
        self.sync_manager.run_syncer()

        self._get_in_sync(20)
