#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path

import psutil
import requests
from arangodb.starter.manager import StarterManager
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
        self.basedir = Path('DC2DC')
        self.cleanup()
        self.sync_instance = None
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
        self.cluster1["instance"].run_starter()
        while not self.cluster1["instance"].is_instance_up():
            logging.info('.')
            time.sleep(1)
        self.cluster1["instance"].detect_logfiles()
        self.cluster1['smport'] = self.cluster1[
            "instance"].get_sync_master_port()
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.publicip,
            port=str(self.cluster1['smport']))
        reply = requests.get(url)
        logging.info(str(reply))

        self.cluster2["instance"].run_starter()
        while not self.cluster2["instance"].is_instance_up():
            logging.info('.')
            time.sleep(1)
        self.cluster2["instance"].detect_logfiles()
        self.cluster2['smport'] = self.cluster2[
            "instance"].get_sync_master_port()
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.publicip,
            port=str(self.cluster2['smport']))
        reply = requests.get(url)
        logging.info(str(reply))

        cmd = ['arangosync', 'configure', 'sync',
               '--master.endpoint=https://'
               + self.basecfg.publicip
               + ':'
               + str(self.cluster1['smport']),
               '--master.keyfile=' + str(self.ca["clientkeyfile"]),
               '--source.endpoint=https://'
               + self.basecfg.publicip
               + ':'
               + str(self.cluster2['smport']),
               '--master.cacert=' + str(self.ca["cert"]),
               '--source.cacert=' + str(self.ca["cert"]),
               '--auth.keyfile=' + str(self.ca["clientkeyfile"])]
        logging.info(str(cmd))
        self.sync_instance = psutil.Popen(cmd)

    def run(self):
        logging.info('Check status of cluster 1')
        psutil.Popen(
            ['arangosync', 'get', 'status',
             '--master.cacert=' + str(self.ca["cert"]),
             '--master.endpoint=https://{url}:{port}'.format(
                 url=self.basecfg.publicip,
                 port=str(self.cluster1['smport'])),
             '--auth.keyfile=' + str(self.ca["clientkeyfile"]),
             '--verbose']).wait()
        logging.info('Check status of cluster 2')
        psutil.Popen(
            ['arangosync', 'get', 'status',
             '--master.cacert=' + str(self.ca["cert"]),
             '--master.endpoint=https://{url}:{port}'.format(
                 url=self.basecfg.publicip,
                 port=str(self.cluster2['smport'])),
             '--auth.keyfile=' + str(self.ca["clientkeyfile"]),
             '--verbose']).wait()
        logging.info('finished')

    def post_setup(self):
        pass

    def jam_attempt(self):
        pass

    def shutdown(self):
        print('shutting down')
        self.sync_instance.terminate()
        self.sync_instance.wait(timeout=60)
        self.cluster1["instance"].terminate_instance()
        self.cluster2["instance"].terminate_instance()
