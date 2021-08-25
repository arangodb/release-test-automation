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
from tools.versionhelper import is_higher_version

SYNC_VERSIONS = {
    "140": semver.VersionInfo.parse('1.4.0'),
    "150": semver.VersionInfo.parse('1.5.0'),
    "220": semver.VersionInfo.parse('2.2.0'),
    "230": semver.VersionInfo.parse('2.3.0')
}
USERS_ERROR_RX = re.compile('.*\n*.*\n*.*\n*.*(_users).*DIFFERENT.*', re.MULTILINE)
STATUS_INACTIVE = "inactive"


def _create_headers(token):
    return {'Authorization': 'Bearer ' + token,
            "X-Allow-Forward-To-Leader": "true"}


def _get_sync_status(cluster):
    """
        Get status of the replication.
    """
    cluster_instance = cluster['instance']
    token = cluster_instance.get_jwt_token_from_secret_file(cluster["SyncSecret"])
    url = 'https://' + cluster_instance.get_sync_master().get_public_plain_url() + '/_api/sync'
    response = requests.get(url,
                            headers=_create_headers(token),
                            verify=False)

    if response.status_code != 200:
        raise Exception("could not fetch arangosync version from {url}, status code: {status_code}".
                        format(url=url, status_code=response.status_code))

    # Check the incoming status of the cluster.
    incoming_status = STATUS_INACTIVE
    shards = response.json().get('shards')
    if shards and len(shards) > 0:
        # It is the response from the target or proxy cluster.
        incoming_status = response.json().get('status')
        if not incoming_status:
            raise Exception("missing incoming status in response from {url}".format(url=url))

    # Check the outgoing status of the cluster.
    outgoing_status = STATUS_INACTIVE
    outgoing = response.json().get('outgoing')
    if outgoing and len(outgoing) > 0:
        # It is the response from the source or proxy cluster.
        outgoing_status = outgoing[0].get('status')
        if not outgoing_status:
            raise Exception("missing outgoing status in response from {url}".format(url=url))

    # Return status.
    if outgoing_status == STATUS_INACTIVE and incoming_status == STATUS_INACTIVE:
        return STATUS_INACTIVE

    if outgoing_status == STATUS_INACTIVE:
        return incoming_status

    return outgoing_status


class Dc2Dc(Runner):
    """ this launches two clusters in dc2dc mode """
    # pylint: disable=R0913 disable=R0902
    def __init__(self, runner_type, abort_on_error, installer_set,
                 selenium, selenium_driver_args,
                 testrun_name: str):
        super().__init__(runner_type, abort_on_error, installer_set,
                         PunnerProperties('DC2DC', 0, 4500, True),
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
        self.min_replication_factor = 2
        # self.hot_backup = False

    def starter_prepare_env_impl(self):
        def cert_op(args):
            print(args)
            create_cert = psutil.Popen([self.cfg.bin_dir / 'arangodb',
                                        'create'] +
                                       args)
            print("creating cert with PID:" + str(create_cert.pid))
            create_cert.wait()
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
        (success, output, _, _) = self.sync_manager.run_syncer()
        if not success:
            raise Exception("starting the synchronisation failed!" + str(output))
        self.progress(True, "SyncManager: up %s", output)

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

    def _is_higher_sync_version(self, min_v1_version, min_v2_version):
        """ check if the current arangosync version is higher than expected minimum version """
        if self.sync_version.major == 1:
            # It is version 1.y.z so it should be compared to the expected min_v1_version.
            return is_higher_version(self.sync_version, min_v1_version)

        return is_higher_version(self.sync_version, min_v2_version)

    def _get_sync_version(self):
        """
        Check version of the arangosync master on the first cluster
        """
        cluster_instance = self.cluster1['instance']

        token = cluster_instance.get_jwt_token_from_secret_file(self.cluster1["SyncSecret"])
        url = cluster_instance.get_sync_master().get_public_plain_url()
        url = 'https://' + url + '/_api/version'
        response = requests.get(url,
                                headers=_create_headers(token),
                                verify=False)

        if response.status_code != 200:
            raise Exception("could not fetch arangosync version from {0}".format(url))

        version = response.json().get('version')
        if not version:
            raise Exception("missing version in reponse from {0}".format(url))
        print("Arangosync v%s detected" % version)
        return semver.VersionInfo.parse(version)

    def _stop_sync(self, timeout=120):
        output = ""
        success = True

        if self._is_higher_sync_version(SYNC_VERSIONS['150'], SYNC_VERSIONS['230']):
            success, output, _, _ = self.sync_manager.stop_sync(timeout)
        else:
            # Arangosync with the bug for checking in-sync status.
            self.progress(True, "arangosync: stopping sync without checking if shards are in-sync")
            success, output, _, _ = self.sync_manager.stop_sync(timeout, ['--ensure-in-sync=false'])

        if not success:
            self.state += "\n" + output
            raise Exception("failed to stop the synchronization")

        count = 0
        status_source = ""
        status_target = ""
        while count < 30:
            status_source = _get_sync_status(self.cluster1)
            status_target = _get_sync_status(self.cluster2)
            if status_source == STATUS_INACTIVE and status_target == STATUS_INACTIVE:
                return

            count += 1
            time.sleep(2)

        raise Exception("failed to stop the synchronization, source status: "+status_source+", target status: "+status_target)

    def _mitigate_known_issues(self, last_sync_output):
        """
        this function contains counter measures against known issues of arangosync
        """
        print(last_sync_output)
        if last_sync_output.find(
                'temporary failure with http status code: 503: service unavailable') >= 0:
            if self._is_higher_sync_version(SYNC_VERSIONS['140'], SYNC_VERSIONS['220']):
                self.progress(
                    True,
                    'arangosync: {0} does not qualify for restart workaround..'.format(
                        str(self.sync_version))
                )
            else:
                self.progress(True, 'arangosync: restarting instances...')
                self.cluster1["instance"].kill_sync_processes()
                self.cluster2["instance"].kill_sync_processes()
                time.sleep(3)
                self.cluster1["instance"].detect_instances()
                self.cluster2["instance"].detect_instances()
        elif last_sync_output.find('Shard is not turned on for synchronizing') >= 0:
            self.progress(True, 'arangosync: sync in progress.')
        elif re.match(USERS_ERROR_RX, last_sync_output):
            self.progress(True, 'arangosync: resetting users collection...')
            self.sync_manager.reset_failed_shard('_system', '_users')
        else:
            self.progress(True, 'arangosync: unknown error condition, doing nothing.')

    def _get_in_sync(self, attempts):
        self.progress(True, "waiting for the DCs to get in sync")
        output = None
        for count in range (attempts):
            (result, output) = self.sync_manager.check_sync()
            if result:
                print("CHECK SYNC OK!")
                break
            progress("sx" + str(count))
            self._mitigate_known_issues(output)
            time.sleep(10)
        else:
            self.state += "\n" + output
            raise Exception("failed to get the sync status")

    def test_setup_impl(self):
        ret = self.cluster1['instance'].arangosh.check_test_data(
            "dc2dc (post setup - dc1)", True)
        if not [0]:
            raise Exception("check data on source cluster failed " + ret[1])
        self._get_in_sync(20)

        ret = self.cluster2['instance'].arangosh.check_test_data("dc2dc (post setup - dc2)",
                                                                 True, [
                                                                     "--readOnly", "true"
                                                                 ])
        if not ret[0]:
            if not self.cfg.verbose:
                print(ret[1])
            raise Exception("error during verifying of "
                            "the test data on the target cluster " + ret[1])

        args = [
                self.cluster2['instance'].get_frontend().get_public_url(
                    'root:%s@'%self.passvoid)]
        if self.cfg.semver.major >= 3 and self.cfg.semver.minor >= 8:
            args += [
                '--jwt1', self.cluster1['instance'].get_jwt_token_from_secret_file(
                    self.cluster1['instance'].jwtfile),
                '--jwt2', self.cluster2['instance'].get_jwt_token_from_secret_file(
                    self.cluster2['instance'].jwtfile)
            ]

        res = self.cluster1['instance'].arangosh.run_in_arangosh(
            (
                self.cfg.test_data_dir /
                Path('tests/js/server/replication/fuzz/replication-fuzz-global.js')
            ),
            [],
            args
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
        """ rolling upgrade this installation """
        self._stop_sync(300)
        print('aoeu'*30)
        print(self.cfg)
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
        self.cluster1["instance"].detect_instances()
        self.cluster2["instance"].wait_for_upgrade(300)
        self.cluster2["instance"].detect_instances()
        # self.sync_manager.start_sync()
        self.sync_manager.run_syncer()

        self.sync_version = self._get_sync_version()
        self.sync_manager.check_sync_status(0)
        self.sync_manager.check_sync_status(1)
        self.sync_manager.get_sync_tasks(0)
        self.sync_manager.get_sync_tasks(1)
        for node in self.starter_instances:
            node.detect_instance_pids()

    def upgrade_arangod_version_manual_impl(self):
        """ manual upgrade this installation """
        self._stop_sync(300)
        self.sync_manager.replace_binary_for_upgrade(self.new_cfg)
        self.progress(True, "manual upgrade step 1 - stop instances")
        self.starter_instances[0].maintainance(False, InstanceType.COORDINATOR)
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_cfg, False)
        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()

        self.progress(True, "step 2 - upgrade agents")
        for node in self.starter_instances:
            node.upgrade_instances([
                InstanceType.AGENT
            ], ['--database.auto-upgrade', 'true',
                '--log.foreground-tty', 'true'])
        self.progress(True, "step 3 - upgrade db-servers")
        for node in self.starter_instances:
            node.upgrade_instances([
                InstanceType.DBSERVER
            ], ['--database.auto-upgrade', 'true',
                '--log.foreground-tty', 'true'])
        self.progress(True, "step 4 - coordinator upgrade")
        # now the new cluster is running. we will now run the coordinator upgrades
        for node in self.starter_instances:
            logging.info("upgrading coordinator instances\n" + str(node))
            node.upgrade_instances([
                InstanceType.COORDINATOR
            ], [
                '--database.auto-upgrade', 'true'
            ])
        self.progress(True, "step 5 restart the full cluster ")
        for node in self.starter_instances:
            node.respawn_instance()
        self.progress(True, "step 6 wait for the cluster to be up")
        for node in self.starter_instances:
            node.detect_instances()
            node.wait_for_version_reply()

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
        ret = self.cluster2["instance"].arangosh.check_test_data(
            "cluster1 after dissolving", True)
        if not ret[0]:
            raise Exception("check data on cluster 1 after dissolving failed " + ret[1])
        ret = self.cluster2["instance"].arangosh.check_test_data(
            "cluster2 after dissolving", True)
        if not ret[0]:
            raise Exception("check data on cluster2 after dissolving failed " + ret[1])
        self.progress(True, "restarting sync")
        self._launch_sync(True)
        self._get_in_sync(20)
        ret = self.cluster2["instance"].arangosh.check_test_data(
                "cluster2 after re-syncing",
                True
                , [
                    "--readOnly", "true"
                ])
        if not ret[0]:
            raise Exception("check data on cluster1 failed after re-sync \n" + ret[1])
        ret =self.cluster1["instance"].arangosh.check_test_data(
                "cluster1 after re-syncing", True)
        if not ret[0]:
            raise Exception("check data on cluster1 failed after re-sync " + ret[1])

        self.progress(True, "checking whether volatile data has been removed from both DCs")
        if (not self.cluster1["instance"].arangosh.hotbackup_check_for_nonbackup_data() or
            not self.cluster2["instance"].arangosh.hotbackup_check_for_nonbackup_data()):
            raise Exception("expected data created on disconnected follower DC to be gone!")

        self.progress(True, "stopping sync")
        self._stop_sync(120)
        self.progress(True, "reversing sync direction")
        self._launch_sync(False)
        self._get_in_sync(20)
        ret = self.cluster2["instance"].arangosh.check_test_data(
            "cluster2 after reversing direction", True)
        if not ret[0]:
            raise Exception("check data on cluster 2 failed after reversing " + ret[1])

    def shutdown_impl(self):
        self.cluster1["instance"].terminate_instance()
        self.cluster2["instance"].terminate_instance()

    def before_backup_impl(self):
        self.sync_manager.abort_sync()

    def after_backup_impl(self):
        self.sync_manager.run_syncer()

        self._get_in_sync(20)
