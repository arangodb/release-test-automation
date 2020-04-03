#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import datetime
import time
import shutil
from logging import info as log
import logging
from enum import Enum
from pathlib import Path
from abc import abstractmethod

import psutil
import requests
from startermanager import StarterManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def timestamp():
    """ get the formated "now" timestamp"""
    return datetime.datetime.utcnow().isoformat()

class RunnerType(Enum):
    """ dial which runner instance you want"""
    LEADER_FOLLOWER = 1
    ACTIVE_FAILOVER = 2
    CLUSTER = 3
    DC2DC = 4

class Runner():
    """abstract starter environment runner"""

    @abstractmethod
    def setup(self):
        """ base setup; declare instance variables etc """

    @abstractmethod
    def run(self):
        """ now launch the stuff"""

    @abstractmethod
    def post_setup(self):
        """ setup steps after the basic instances were launched """

    @abstractmethod
    def jam_attempt(self):
        """ check resilience of setup by obstructing its instances """

    @abstractmethod
    def shutdown(self):
        """ stop everything """

    def cleanup(self):
        """ remove all directories created by this test """
        testdir = self.basecfg.baseTestDir / self.basedir
        if testdir.exists():
            shutil.rmtree(testdir)

class LeaderFollower(Runner):
    """ this runs a leader / Follower setup with synchronisation """
    def __init__(self, cfg):
        log("x"*80)
        log("xx           Leader Follower Test      ")
        log("x"*80)
        self.leader = None
        self.follower = None
        self.success = True
        self.basecfg = cfg
        self.basedir = Path('lf')
        self.cleanup()
        self.checks = {
            "beforeReplJS": ("""
db._create("testCollectionBefore");
db.testCollectionBefore.save({"hello": "world"})
""", "saving document before"),
            "afterReplJS": ("""
db._create("testCollectionAfter");
db.testCollectionAfter.save({"hello": "world"})
""", "saving document after the replication"),
            "checkReplJS": ("""
if (!db.testCollectionBefore.toArray()[0]["hello"] === "world") {
  throw new Error("before not yet there?");
}
if (!db.testCollectionAfter.toArray()[0]["hello"] === "world") {
  throw new Error("after not yet there?");
}
""", "checking documents")}

    def setup(self):
        self.leader = StarterManager(self.basecfg,
                                     self.basedir / 'leader',
                                     mode='single',
                                     port=1234,
                                     moreopts=[])
        self.follower = StarterManager(self.basecfg,
                                       self.basedir / 'follower',
                                       mode='single',
                                       port=2345,
                                       moreopts=[])

    def run(self):
        self.leader.run_starter()
        self.follower.run_starter()
        log(str(self.leader.execute_frontend(self.checks['beforeReplJS'])))
        self.checks['startReplJS'] = ("""
require("@arangodb/replication").setupReplicationGlobal({
    endpoint: "tcp://127.0.0.1:%d",
    username: "root",
    password: "",
    verbose: false,
    includeSystem: true,
    incremental: true,
    autoResync: true
    });
""" % (self.leader.get_frontend_port()), "launching replication")
        log(str(self.follower.execute_frontend(self.checks['startReplJS'])))
        log(str(self.leader.execute_frontend(self.checks['afterReplJS'])))
    def post_setup(self):

        log("checking for the replication")

        count = 0
        while count < 30:
            if self.follower.execute_frontend(self.checks['checkReplJS']):
                break
            log(".")
            time.sleep(1)
            count += 1
        if count > 29:
            raise Exception("replication didn't make it in 30s!")
        log("all OK!")

    def jam_attempt(self):
        pass

    def shutdown(self):
        self.leader.kill_instance()
        self.follower.kill_instance()
        log('test ended')


class ActiveFailover(Runner):
    """ This launches an active failover setup """
    def __init__(self, cfg):
        log("x"*80)
        log("xx           Active Failover Test      ")
        log("x"*80)
        self.success = True
        self.basecfg = cfg
        self.basedir = Path('AFO')
        self.cleanup()
        self.starter_instances = []
        self.follower_nodes = None
        self.leader = None
        self.new_leader = None
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node1',
                           mode='activefailover',
                           moreopts=[]))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node2',
                           mode='activefailover',
                           moreopts=['--starter.join', '127.0.0.1']))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node3',
                           mode='activefailover',
                           moreopts=['--starter.join', '127.0.0.1']))
    def setup(self):
        for node in self.starter_instances:
            log("Spawning instance")
            node.run_starter()
        log("waiting for the starters to become alive")
        while (not self.starter_instances[0].is_instance_up()
               and not self.starter_instances[1].is_instance_up()
               and not self.starter_instances[1].is_instance_up()):
            log('.')
            time.sleep(1)
        log("waiting for the cluster instances to become alive")
        for node in self.starter_instances:
            node.detect_logfiles()
            node.active_failover_detect_hosts()
        log("instances are ready, detecting leader")
        self.follower_nodes = []
        while self.leader is None:
            for node in self.starter_instances:
                if node.detect_leader():
                    self.leader = node
                    break
        for node in self.starter_instances:
            node.detect_instance_pids()
            if not node.is_leader:
                self.follower_nodes.append(node)
        log("system ready")

    def run(self):
        log("starting test")
        self.success = True
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.localhost,
            port=self.leader.get_frontend_port())

        reply = requests.get(url)
        log(str(reply))
        if reply.status_code != 200:
            log(reply.text)
            self.success = False
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.localhost,
            port=self.follower_nodes[0].get_frontend_port())
        reply = requests.get(url)
        log(str(reply))
        log(reply.text)
        if reply.status_code != 503:
            self.success = False
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.localhost,
            port=self.follower_nodes[1].get_frontend_port())
        reply = requests.get(url)
        log(str(reply))
        log(reply.text)
        if reply.status_code != 503:
            self.success = False
        log("success" if self.success else "fail")
        log('leader can be reached at: http://%s:%s' % (
            self.basecfg.publicip,
            self.leader.get_frontend_port()))

    def post_setup(self):
        pass
    def jam_attempt(self):
        self.leader.kill_instance()
        log("waiting for new leader...")
        self.new_leader = None
        while self.new_leader is None:
            for node in self.follower_nodes:
                node.detect_leader()
                if node.is_leader:
                    log('have a new leader: ' + str(node.arguments))
                    self.new_leader = node
                    break
                log('.')
            time.sleep(1)
        log(str(self.new_leader))
        url = 'http://{host}:{port}{uri}'.format(
            host=self.basecfg.localhost,
            port=self.new_leader.get_frontend_port(),
            uri='/_db/_system/_admin/aardvark/index.html#replication')
        reply = requests.get(url)
        log(str(reply))
        if reply.status_code != 200:
            log(reply.text)
            self.success = False
        log('new leader can be reached at: http://%s:%s' % (
            self.basecfg.publicip, self.leader.get_frontend_port()))
        input("Press Enter to continue...")

        self.leader.respawn_instance()

        log("waiting for old leader to show up as follower")
        while not self.leader.active_failover_detect_host_now_follower():
            log('.')
            time.sleep(1)
        log("Now is follower")
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.localhost,
            port=self.leader.get_frontend_port())
        reply = requests.get(url)
        log(str(reply))
        log(str(reply.text))
        if reply.status_code != 503:
            self.success = False
        log("state of this test is: " + "Success" if self.success else "Failed")

    def shutdown(self):
        for node in self.starter_instances:
            node.kill_instance()
        log('test ended')


class Cluster(Runner):
    """ this launches a cluster setup """
    def __init__(self, cfg):
        log("x"*80)
        log("xx           cluster test      ")
        log("x"*80)
        self.success = True
        self.create_test_collection = ("""
db._create("testCollection",  { numberOfShards: 6, replicationFactor: 2});
db.testCollection.save({test: "document"})
""", "create test collection")
        self.basecfg = cfg
        self.basedir = Path('CLUSTER')
        self.cleanup()
        self.starter_instances = []
        self.jwtdatastr = str(timestamp())
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node1',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           moreopts=[]))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node2',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           moreopts=['--starter.join', '127.0.0.1']))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node3',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           moreopts=['--starter.join', '127.0.0.1']))
    def setup(self):
        for node in self.starter_instances:
            log("Spawning instance")
            node.run_starter()
        log("waiting for the starters to become alive")
        while (not self.starter_instances[0].is_instance_up()
               and not self.starter_instances[1].is_instance_up()
               and not self.starter_instances[1].is_instance_up()):
            log('.')
            time.sleep(1)
        log("waiting for the cluster instances to become alive")
        for node in self.starter_instances:
            node.detect_logfiles()
            node.detect_instance_pids()
            log('coordinator can be reached at: http://%s:%s' %(
                self.basecfg.publicip, str(node.get_frontend_port())))
        log("instances are ready")

    def run(self):
        input("Press Enter to continue")
        #  TODO self.create_test_collection
        log("stopping instance 2")
        self.starter_instances[2].kill_instance()
        input("Press Enter to continue")
        self.starter_instances[2].respawn_instance()
        input("Press Enter to finish this test")

    def post_setup(self):
        pass
    def jam_attempt(self):
        log('Starting instance without jwt')
        dead_instance = StarterManager(self.basecfg,
                                       Path('CLUSTER') / 'nodeX',
                                       mode='cluster',
                                       jwtStr=None,
                                       moreopts=['--starter.join', '127.0.0.1'])
        dead_instance.run_starter()
        i = 0
        while True:
            log("." + str(i))
            if not dead_instance.is_instance_running():
                break
            if i > 40:
                log('Giving up wating for the starter to exit')
                raise Exception("non-jwt-ed starter won't exit")
            i += 1
            time.sleep(10)
        log(str(dead_instance.instance.wait(timeout=320)))
        log('dead instance is dead?')

    def shutdown(self):
        for node in self.starter_instances:
            node.kill_instance()
        log('test ended')

class Dc2Dc(Runner):
    """ this launches two clusters in dc2dc mode """
    def __init__(self, cfg):
        def cert_op(args):
            print(args)
            psutil.Popen([self.basecfg.installPrefix
                          / 'usr' / 'bin' / 'arangodb',
                          'create'] +
                         args).wait()
        log("x"*80)
        log("xx           dc 2 dc test      ")
        log("x"*80)
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
                "dir": self.basedir / self.basecfg.baseTestDir / self.basedir / datadir / subdir,
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
        log('Create TLS certificates')
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
        log('Create client authentication certificates')
        cert_op(['client-auth', 'ca',
                 '--cert=' + str(client_cert),
                 '--key=' + str(self.ca["clientauth_key"])])
        cert_op(['client-auth', 'keyfile',
                 '--cacert=' + str(client_cert),
                 '--cakey=' + str(self.ca["clientauth_key"]),
                 '--keyfile=' + str(self.ca["clientkeyfile"])])
        log('Create JWT secrets')
        for node in [self.cluster1, self.cluster2]:
            cert_op(['jwt-secret', '--secret=' + str(node["SyncSecret"])])
            cert_op(['jwt-secret', '--secret=' + str(node["JWTSecret"])])

        def add_starter(val, port):
            val["instance"] = StarterManager(
                self.basecfg,
                val["dir"],
                port=port,
                mode='cluster',
                moreopts=
                ['--starter.sync'
                 , '--starter.local'
                 , '--auth.jwt-secret=' +           str(val["JWTSecret"])
                 , '--sync.server.keyfile=' +       str(val["tlsKeyfile"])
                 , '--sync.server.client-cafile=' + str(client_cert)
                 , '--sync.master.jwt-secret=' +    str(val["SyncSecret"])
                 , '--starter.address=' +           self.basecfg.publicip
                ])
        add_starter(self.cluster1, None)
        add_starter(self.cluster2, port=9528)

    def setup(self):
        self.cluster1["instance"].run_starter()
        while not self.cluster1["instance"].is_instance_up():
            log('.')
            time.sleep(1)
        self.cluster1["instance"].detect_logfiles()
        self.cluster1['smport'] = self.cluster1["instance"].get_sync_master_port()
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.publicip,
            port=str(self.cluster1['smport']))
        reply = requests.get(url)
        log(str(reply))

        self.cluster2["instance"].run_starter()
        while not self.cluster2["instance"].is_instance_up():
            log('.')
            time.sleep(1)
        self.cluster2["instance"].detect_logfiles()
        self.cluster2['smport'] = self.cluster2["instance"].get_sync_master_port()
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.publicip,
            port=str(self.cluster2['smport']))
        reply = requests.get(url)
        log(str(reply))

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
        log(str(cmd))
        self.sync_instance = psutil.Popen(cmd)

    def run(self):
        log('Check status of cluster 1')
        psutil.Popen(
            ['arangosync', 'get', 'status',
             '--master.cacert=' + str(self.ca["cert"]),
             '--master.endpoint=https://{url}:{port}'.format(
                 url=self.basecfg.publicip,
                 port=str(self.cluster1['smport'])),
             '--auth.keyfile=' + str(self.ca["clientkeyfile"]),
             '--verbose']).wait()
        log('Check status of cluster 2')
        psutil.Popen(
            ['arangosync', 'get', 'status',
             '--master.cacert=' + str(self.ca["cert"]),
             '--master.endpoint=https://{url}:{port}'.format(
                 url=self.basecfg.publicip,
                 port=str(self.cluster2['smport'])),
             '--auth.keyfile=' + str(self.ca["clientkeyfile"]),
             '--verbose']).wait()
        log('finished')
    def post_setup(self):
        pass
    def jam_attempt(self):
        pass
    def shutdown(self):
        print('shutting down')
        self.sync_instance.terminate()
        self.sync_instance.wait(timeout=60)
        self.cluster1["instance"].kill_instance()
        self.cluster2["instance"].kill_instance()

def get(typeof, baseconfig):
    """ get an instance of the arangod runner - as you specify """
    print("get!")
    if typeof == RunnerType.LEADER_FOLLOWER:
        return LeaderFollower(baseconfig)

    if typeof == RunnerType.ACTIVE_FAILOVER:
        return ActiveFailover(baseconfig)

    if typeof == RunnerType.CLUSTER:
        return Cluster(baseconfig)

    if typeof == RunnerType.DC2DC:
        return Dc2Dc(baseconfig)
    raise Exception("unknown starter type")
