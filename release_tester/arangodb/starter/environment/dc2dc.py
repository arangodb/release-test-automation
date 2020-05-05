#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path

import psutil
import requests
from arangodb.starter.manager import StarterManager
from arangodb.sync import SyncManager
from arangodb.starter.environment.runner import Runner

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class Dc2Dc(Runner):
    """ this launches two clusters in dc2dc mode """
    def __init__(self, cfg):
        def cert_op(args):
            print(args)
            psutil.Popen([self.basecfg.installPrefix
                          / 'usr' / 'bin' / 'arangodb',
                          'create'] +
                         args).wait()
        logging.info("x"*80)
        logging.info("xx           dc 2 dc test      ")
        logging.info("x"*80)
        self.success = True
        self.basecfg = cfg
        self.basecfg.passvoid = '' # TODO
        self.basedir = Path('DC2DC')
        self.cleanup()
        self.sync_manager = None
        datadir = Path('data')
        cert_dir = self.basecfg.baseTestDir / self.basedir / "certs"
        print(cert_dir)
        cert_dir.mkdir(parents=True, exist_ok=True)
        cert_dir.mkdir(parents=True, exist_ok=True)

        def getdirs(subdir):
            return {
                "dir": self.basedir /
                       self.basecfg.baseTestDir /
                       self.basedir / datadir / subdir,
                "SyncSecret": cert_dir / subdir / 'syncmaster.jwtsecret',
                "JWTSecret": cert_dir / subdir / 'arangodb.jwtsecret',
                "tlsKeyfile": cert_dir / subdir / 'tls.keyfile',
            }

        self.cluster1 = getdirs(Path('custer1'))
        self.cluster2 = getdirs(Path('custer2'))
        client_cert = cert_dir / 'client-auth-ca.crt'
        self.ca = {
            "cert": cert_dir / 'tls-ca.crt',
            "key": cert_dir / 'tls-ca.key',
            "clientauth_key": cert_dir / 'client-auth-ca.key',
            "clientkeyfile": cert_dir / 'client-auth-ca.keyfile'
        }
        logging.info('Create TLS certificates')
        cert_op(['tls', 'ca',
                 '--cert=' + str(self.ca["cert"]),
                 '--key=' + str(self.ca["key"])])
        cert_op(['tls', 'keyfile',
                 '--cacert=' + str(self.ca["cert"]),
                 '--cakey=' + str(self.ca["key"]),
                 '--keyfile=' + str(self.cluster1["tlsKeyfile"]),
                 '--host=' + self.basecfg.publicip, '--host=localhost'])
        cert_op(['tls', 'keyfile',
                 '--cacert=' + str(self.ca["cert"]),
                 '--cakey=' + str(self.ca["key"]),
                 '--keyfile=' + str(self.cluster2["tlsKeyfile"]),
                 '--host=' + self.basecfg.publicip, '--host=localhost'])
        logging.info('Create client authentication certificates')
        cert_op(['client-auth', 'ca',
                 '--cert=' + str(client_cert),
                 '--key=' + str(self.ca["clientauth_key"])])
        cert_op(['client-auth', 'keyfile',
                 '--cacert=' + str(client_cert),
                 '--cakey=' + str(self.ca["clientauth_key"]),
                 '--keyfile=' + str(self.ca["clientkeyfile"])])
        logging.info('Create JWT secrets')
        for node in [self.cluster1, self.cluster2]:
            cert_op(['jwt-secret', '--secret=' + str(node["SyncSecret"])])
            cert_op(['jwt-secret', '--secret=' + str(node["JWTSecret"])])

        def add_starter(val, port):
            val["instance"] = StarterManager(
                self.basecfg,
                val["dir"],
                port=port,
                mode='cluster',
                moreopts=[
                    '--starter.sync',
                    '--starter.local',
                    '--auth.jwt-secret=' +           str(val["JWTSecret"]),
                    '--sync.server.keyfile=' +       str(val["tlsKeyfile"]),
                    '--sync.server.client-cafile=' + str(client_cert),
                    '--sync.master.jwt-secret=' +    str(val["SyncSecret"]),
                    '--starter.address=' +           self.basecfg.publicip
                ])
        add_starter(self.cluster1, None)
        add_starter(self.cluster2, port=9528)

    def setup(self):
        def launch(cluster):
            inst = cluster["instance"]
            inst.run_starter()
            while not inst.is_instance_up():
                logging.info('.')
                time.sleep(1)
            inst.detect_logfiles()
            inst.detect_instance_pids()
            cluster['smport'] = inst.get_sync_master_port()

            url = 'http://{host}:{port}'.format(
                host=self.basecfg.publicip,
                port=str(cluster['smport']))
            reply = requests.get(url)
            logging.info(str(reply))
            logging.info(str(reply.raw))


        launch(self.cluster1)
        launch(self.cluster2)

        self.sync_manager = SyncManager(self.basecfg,
                                        self.ca,
                                        [self.cluster2['smport'],
                                         self.cluster1['smport'] ] )
        if not self.sync_manager.run_syncer():
            raise Exception("starting the synchronisation failed!")
        time.sleep(60) # TODO: howto detect dc2dc is completely up and running?

    def run(self):
        logging.info('finished')
        
    def post_setup(self):
        self.cluster1['instance'].arangosh.create_test_data()
        self.sync_manager.check_sync_status(0)
        self.sync_manager.check_sync_status(1)
        self.sync_manager.get_sync_tasks(0)
        self.sync_manager.get_sync_tasks(1)
        time.sleep(180) # TODO: howto detect dc2dc is completely up and running?
        # exit(0)
        self.sync_manager.check_sync_status(0)
        self.sync_manager.check_sync_status(1)
        self.sync_manager.get_sync_tasks(0)
        self.sync_manager.get_sync_tasks(1)
        
        pass

    def upgrade(self, newInstallCfg):
        """ upgrade this installation """
        self.sync_manager.replace_binary_for_upgrade(newInstallCfg)
        self.sync_manager.stop_sync()
        self.cluster1["instance"].replace_binary_for_upgrade(newInstallCfg)
        self.cluster2["instance"].replace_binary_for_upgrade(newInstallCfg)
        self.cluster1["instance"].detect_instance_pids_still_alive()
        self.cluster2["instance"].detect_instance_pids_still_alive()
        self.cluster1["instance"].command_upgrade()
        self.cluster2["instance"].command_upgrade()
        self.cluster1["instance"].wait_for_upgrade()
        self.cluster2["instance"].wait_for_upgrade()
        self.sync_manager.respawn_instance()
        time.sleep(180) # TODO: howto detect dc2dc is completely up and running?
        self.sync_manager.check_sync_status(0)
        self.sync_manager.check_sync_status(1)
        self.sync_manager.get_sync_tasks(0)
        self.sync_manager.get_sync_tasks(1)
        # exit(0)

    def jam_attempt(self):
        pass

    def shutdown(self):
        print('shutting down')
        self.sync_manager.terminate_instance()
        self.cluster1["instance"].terminate_instance()
        self.cluster2["instance"].terminate_instance()
