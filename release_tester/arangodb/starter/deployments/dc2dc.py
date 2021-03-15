#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path

import psutil
import requests
import semver
from arangodb.starter.manager import StarterManager
from arangodb.sync import SyncManager
from arangodb.starter.deployments.runner import Runner
from arangodb.instance import InstanceType

class Dc2Dc(Runner):
    """ this launches two clusters in dc2dc mode """
    # pylint: disable=R0913 disable=R0902
    def __init__(self, runner_type, cfg, old_inst, new_cfg, new_inst,
                 selenium, selenium_driver_args):
        super().__init__(runner_type, cfg, old_inst, new_cfg, new_inst,
                         'DC2DC', 0, 3500, selenium, selenium_driver_args)
        self.success = True
        self.cfg.passvoid = '' # TODO
        self.sync_manager = None
        self.cluster1 = {}
        self.cluster2 = {}
        self.certificate_auth = {}

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
                    InstanceType.agent,
                    InstanceType.agent,
                    InstanceType.agent,
                    InstanceType.coordinator,
                    InstanceType.coordinator,
                    InstanceType.coordinator,
                    InstanceType.dbserver,
                    InstanceType.dbserver,
                    InstanceType.dbserver,
                    InstanceType.syncmaster,
                    InstanceType.syncmaster,
                    InstanceType.syncmaster,
                    InstanceType.syncworker,
                    InstanceType.syncworker,
                    InstanceType.syncworker
                ],
                moreopts=[
                    '--starter.sync',
                    '--starter.local',
                    '--auth.jwt-secret=' +           str(val["JWTSecret"]),
                    '--sync.server.keyfile=' +       str(val["tlsKeyfile"]),
                    '--sync.server.client-cafile=' + str(client_cert),
                    '--sync.master.jwt-secret=' +    str(val["SyncSecret"]),
                    '--starter.address=' +           self.cfg.publicip
                ])
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

    def finish_setup_impl(self):
        version = self.get_sync_version()
        self.sync_manager = SyncManager(self.cfg,
                                        self.certificate_auth,
                                        [self.cluster2['smport'],
                                         self.cluster1['smport']],
                                        version)

        if not self.sync_manager.run_syncer():
            raise Exception("starting the synchronisation failed!")

        self.makedata_instances = [ self.cluster1['instance'] ]
        self.set_frontend_instances()
        count = 0
        for node in self.starter_instances:
            node.set_passvoid('dc2dc', count == 0)
            count += 1
        self.passvoid = 'dc2dc'

    def get_sync_version(self):
        """
        Check version of the arangosync master on the first cluster
        """
        cluster_instance = self.cluster1['instance']

        token = cluster_instance.get_jwt_token_from_secret_file(self.cluster1["SyncSecret"])
        url = 'https://' + cluster_instance.get_sync_master().get_public_plain_url() + '/_api/version'
        response = requests.get(url, headers={'Authorization': 'Bearer ' + token}, verify=False)

        if response.status_code != 200:
            raise Exception("could not fetch arangosync version from {0}".format(url))

        version = response.json().get('version')
        if not version:
            raise Exception("missing version in reponse from {0}".format(url))

        return semver.VersionInfo.parse(version)

    def test_setup_impl(self):
        self.cluster1['instance'].arangosh.check_test_data("dc2dc (post setup - dc1)")
        count = 0
        while not self.sync_manager.check_sync():
            if count > 20:
                raise Exception("failed to get the sync status")
            time.sleep(10)
            count += 1
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
        if not self.sync_manager.check_sync():
            raise Exception("failed to get the sync status")

    def upgrade_arangod_version_impl(self):
        """ upgrade this installation """
        self.sync_manager.replace_binary_for_upgrade(self.new_cfg)
        self.cluster1["instance"].replace_binary_for_upgrade(self.new_cfg)
        self.cluster2["instance"].replace_binary_for_upgrade(self.new_cfg)
        self.cluster1["instance"].detect_instance_pids_still_alive()
        self.cluster2["instance"].detect_instance_pids_still_alive()
        self.cluster1["instance"].command_upgrade()
        self.cluster2["instance"].command_upgrade()

        # workaround: kill the sync'ers by hand, the starter doesn't
        # self.sync_manager.stop_sync()
        self.cluster1["instance"].kill_sync_processes()
        self.cluster2["instance"].kill_sync_processes()

        self.cluster1["instance"].wait_for_upgrade()
        self.cluster2["instance"].wait_for_upgrade()

        # self.sync_manager.start_sync()

        self.cluster1["instance"].detect_instances()
        self.cluster2["instance"].detect_instances()

        self.sync_manager.check_sync_status(0)
        self.sync_manager.check_sync_status(1)
        self.sync_manager.get_sync_tasks(0)
        self.sync_manager.get_sync_tasks(1)

    def jam_attempt_impl(self):
        pass

    def shutdown_impl(self):
        self.cluster1["instance"].terminate_instance()
        self.cluster2["instance"].terminate_instance()

    def before_backup_impl(self):
        # self.sync_manager.stop_sync()

    def after_backup_impl(self):
        #self.sync_manager.start_sync()
        #count = 0
        #while not self.sync_manager.check_sync():
        #    if count > 20:
        #        raise Exception("failed to get the sync status")
        #    time.sleep(10)
        #    count += 1
