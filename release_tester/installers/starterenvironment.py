import datetime
import time
import requests
from logging import info as log
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
from enum import Enum
from pathlib import Path
from abc import abstractmethod
from startermanager import starterManager
from installers.arangosh import arangoshExecutor
import psutil

def timestamp():
    return datetime.datetime.utcnow().isoformat()

class runnertype(Enum):
    LEADER_FOLLOWER=1
    ACTIVE_FAILOVER=2
    CLUSTER=3
    DC2DC=4

class runner(object):
    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def postSetup(self):
        pass

    @abstractmethod
    def jamAttempt(self):
        pass

    @abstractmethod
    def shutdown(self):
        pass

class LeaderFollower(runner):
    def __init__(self, cfg):
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        log("xx           Leader Follower Test      ")
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.basecfg = cfg
        self.beforeReplJS = ("""
db._create("testCollectionBefore");
db.testCollectionBefore.save({"hello": "world"})
""", "saving document before")
        self.afterReplJS =  ("""
db._create("testCollectionAfter");
db.testCollectionAfter.save({"hello": "world"})
""", "saving document after the replication")
        self.checkReplJS = ("""
if (!db.testCollectionBefore.toArray()[0]["hello"] === "world") {
  throw new Error("before not yet there?");
}
if (!db.testCollectionAfter.toArray()[0]["hello"] === "world") {
  throw new Error("after not yet there?");
}
""", "checking documents")

    def setup(self):
        self.leader = starterManager(self.basecfg,
                                     Path('lf')/ 'leader',
                                     mode='single',
                                     port=1234,
                                     moreopts=[])
        self.follower = starterManager(self.basecfg,
                                       Path('lf') / 'follower',
                                       mode='single',
                                       port=2345,
                                       moreopts=[])

    def run(self):
        self.leader.runStarter()
        self.follower.runStarter()
        log(str(self.leader.executeFrontend(self.beforeReplJS)))
        self.startReplJS = ("""
require("@arangodb/replication").setupReplicationGlobal({
    endpoint: "tcp://127.0.0.1:%d",
    username: "root",
    password: "",
    verbose: false,
    includeSystem: true,
    incremental: true,
    autoResync: true
    });
""" % (self.leader.getFrontendPort()), "launching replication")
        log(str(self.follower.executeFrontend(self.startReplJS)))
        log(str(self.leader.executeFrontend(self.afterReplJS)))
    def postSetup(self):

        log("checking for the replication")

        count = 0
        while count < 30:
            if self.follower.executeFrontend(self.checkReplJS):
                break
            log(".")
            time.sleep(1)
            count += 1
        if (count > 29):
            raise Exception("replication didn't make it in 30s!")
        log("all OK!")

    def jamAttempt(self):
        pass

    def shutdown(self):
        self.leader.killInstance()
        self.follower.killInstance()
        log('test ended')

    

class activeFailover(runner):
    def __init__(self, cfg):
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        log("xx           Active Failover Test      ")
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.basecfg = cfg
        self.starterInstances = []
        self.starterInstances.append(starterManager(self.basecfg,
                                                    Path('AFO') / 'node1',
                                                    mode='activefailover',
                                                    moreopts=[]))
        self.starterInstances.append(starterManager(self.basecfg,
                                                    Path('AFO') / 'node2',
                                                    mode='activefailover',
                                                    moreopts=['--starter.join', '127.0.0.1'] ))
        self.starterInstances.append(starterManager(self.basecfg,
                                                    Path('AFO') / 'node3',
                                                    mode='activefailover',
                                                    moreopts=['--starter.join','127.0.0.1']))
    def setup(self):
        for node in self.starterInstances:
            log("Spawning instance")
            node.runStarter()
        log("waiting for the starters to become alive")
        while (not self.starterInstances[0].isInstanceUp()
               and not self.starterInstances[1].isInstanceUp()
               and not self.starterInstances[1].isInstanceUp()):
            log('.')
            time.sleep(1)
        log("waiting for the cluster instances to become alive")
        for node in self.starterInstances:
            node.detectLogfiles()
            node.ActiveFailoverDetectHosts()
        log("instances are ready, detecting leader")
        self.leader = None
        self.followerNodes = []
        while self.leader == None:
            for node in self.starterInstances:
                if node.detectLeader():
                    self.leader = node
                    break
        for node in self.starterInstances:
            node.detectInstancePIDs()
            if not node.isLeader:
                self.followerNodes.append(node)
        log("system ready")
            
        pass
    def run(self):
        log("starting test")
        self.success = True
        r = requests.get('http://ip6-localhost:' + self.leader.getFrontendPort())
        log(str(r))
        if r.status_code != 200:
            log(r.text)
            self.success = False
        log('http://ip6-localhost:' + self.followerNodes[0].getFrontendPort())
        r = requests.get('http://ip6-localhost:' + self.followerNodes[0].getFrontendPort())
        log(str(r))
        log(r.text)
        if r.status_code != 503:
            self.success = False
        log('http://ip6-localhost:' + self.followerNodes[1].getFrontendPort())
        r = requests.get('http://ip6-localhost:' + self.followerNodes[1].getFrontendPort())
        log(str(r))
        log(r.text)
        if r.status_code != 503:
            self.success = False
        log("success" if self.success else "fail")
        log('leader can be reached at: ' + 'http://' + self.basecfg.publicip + ':' + self.leader.getFrontendPort())

    def postSetup(self):
        pass
    def jamAttempt(self):
        self.leader.killInstance()
        log("waiting for new leader...")
        self.newLeader = None
        while self.newLeader == None:
            for node in self.followerNodes:
                node.detectLeader()
                if node.isLeader:
                    log('have a new leader: ' + str(node.arguments))
                    self.newLeader = node;
                    break
                log('.')
            time.sleep(1)
        log(str(self.newLeader))
        r = requests.get('http://ip6-localhost:' + self.newLeader.getFrontendPort() + '/_db/_system/_admin/aardvark/index.html#replication')
        log(str(r))
        if r.status_code != 200:
            log(r.text)
            self.success = False
        log('new leader can be reached at: ' + 'http://' + self.basecfg.publicip + ':' + self.newLeader.getFrontendPort())
        input("Press Enter to continue...")
        
        self.leader.respawnInstance()
    
        log("waiting for old leader to show up as follower")
        while not self.leader.ActiveFailoverDetectHostNowFollower():
            log('.')
            time.sleep(1)
        log("Now is follower")
        r = requests.get('http://ip6-localhost:' + self.leader.getFrontendPort())
        log(str(r))
        log(r.text)
        if r.status_code != 503:
            self.success = False
        log("state of this test is: " + "Success" if self.success else "Failed")
    
    def shutdown(self):
        for node in self.starterInstances:
            node.killInstance()
        log('test ended')




class cluster(runner):
    def __init__(self, cfg):
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        log("xx           cluster test      ")
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.createTestCollection = ("""
db._create("testCollection",  { numberOfShards: 6, replicationFactor: 2});
db.testCollection.save({test: "document"})
""", "create test collection")
        self.basecfg = cfg
        self.starterInstances = []
        self.jwtdatastr = str(timestamp())
        self.starterInstances.append(starterManager(self.basecfg,
                                                    Path('CLUSTER') / 'node1',
                                                    mode='cluster',
                                                    jwtStr=self.jwtdatastr,
                                                    moreopts=[]))
        self.starterInstances.append(starterManager(self.basecfg,
                                                    Path('CLUSTER') / 'node2',
                                                    mode='cluster',
                                                    jwtStr=self.jwtdatastr,
                                                    moreopts=['--starter.join', '127.0.0.1'] ))
        self.starterInstances.append(starterManager(self.basecfg,
                                                    Path('CLUSTER') / 'node3',
                                                    mode='cluster',
                                                    jwtStr=self.jwtdatastr,
                                                    moreopts=['--starter.join','127.0.0.1']))
    def setup(self):
        for node in self.starterInstances:
            log("Spawning instance")
            node.runStarter()
        log("waiting for the starters to become alive")
        while (not self.starterInstances[0].isInstanceUp()
               and not self.starterInstances[1].isInstanceUp()
               and not self.starterInstances[1].isInstanceUp()):
            log('.')
            time.sleep(1)
        log("waiting for the cluster instances to become alive")
        for node in self.starterInstances:
            node.detectLogfiles()
            node.detectInstancePIDs()
            log('coordinator can be reached at: ' + 'http://' + self.basecfg.publicip + ':' + node.getFrontendPort())
        log("instances are ready")

    def run(self):
        input("Press Enter to continue")
        
        log("stopping instance 2")
        self.starterInstances[2].killInstance()
        input("Press Enter to continue")
        self.starterInstances[2].respawnInstance()
        input("Press Enter to finish this test")

    def postSetup(self):
        pass
    def jamAttempt(self):
        log('Starting instance without jwt')
        deadInstance = starterManager(self.basecfg,
                                      Path('CLUSTER') / 'nodeX',
                                      mode='cluster',
                                      jwtStr=None,
                                      moreopts=['--starter.join', '127.0.0.1'])
        deadInstance.runStarter()
        i = 0
        while True:
            log("." + str(i))
            if not deadInstance.isInstanceRunning():
                break
            if i > 40:
                log('Giving up wating for the starter to exit')
                raise Exception("non-jwt-ed starter won't exit")
            i += 1
            time.sleep(10)
        log(str(deadInstance.instance.wait(timeout=320)))
        log('dead instance is dead?')
        pass
    def shutdown(self):
        for node in self.starterInstances:
            node.killInstance()
        log('test ended')

class dc2dc(runner):
    def __init__(self, cfg):
        def certOp(args):
            print(args)
            psutil.Popen([self.basecfg.installPrefix / 'usr' / 'bin' / 'arangodb',
                          'create'] +
                         args).wait()
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        log("xx           dc 2 dc test      ")
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.basecfg = cfg
        self.testdir = Path("DC2DC")
        self.cluster1RelDir = Path('custer1')
        self.cluster2RelDir = Path('custer2')
        self.datadir = Path('data')
        self.certDir = self.basecfg.baseTestDir / self.testdir / "certs"
        print(self.certDir)
        self.certDir.mkdir(parents=True, exist_ok=True)
        self.dataDir = self.basecfg.baseTestDir / self.testdir / self.datadir
        self.certDir.mkdir(parents=True, exist_ok=True)
        self.clientCert = self.certDir / 'client-auth-ca.crt'
        def getdirs(subdir):
            return {"dir": self.testdir / self.datadir / subdir
                   ,"SyncSecret": self.certDir / subdir / 'syncmaster.jwtsecret'
                   ,"JWTSecret": self.certDir / subdir / 'arangodb.jwtsecret'
                   ,"tlsKeyfile": self.certDir / subdir / 'tls.keyfile'
            }
        self.cluster1 = getdirs(self.cluster1RelDir)
        self.cluster2 = getdirs(self.cluster2RelDir)
        self.cacert = self.certDir / 'tls-ca.crt'
        self.cakey = self.certDir / 'tls-ca.key'
        self.clientauthKey = self.certDir / 'client-auth-ca.key'
        self.clientkeyfile = self.certDir / 'client-auth-ca.keyfile'
        log('Create TLS certificates')
        certOp(['tls', 'ca',
                '--cert=' + str(self.cacert),
                '--key=' + str(self.cakey)])
        certOp(['tls', 'keyfile',
                '--cacert=' + str(self.cacert),
                '--cakey=' + str(self.cakey),
                '--keyfile=' + str(self.cluster1["tlsKeyfile"]),
                '--host=' + self.basecfg.publicip, '--host=localhost'])
        certOp(['tls', 'keyfile',
                '--cacert=' + str(self.cacert),
                '--cakey=' + str(self.cakey),
                '--keyfile=' + str(self.cluster2["tlsKeyfile"]),
                '--host=' + self.basecfg.publicip, '--host=localhost'])
        log('Create client authentication certificates')
        certOp(['client-auth', 'ca',
                '--cert=' + str(self.clientCert),
                '--key=' + str(self.clientauthKey)])
        certOp(['client-auth', 'keyfile',
                '--cacert=' + str(self.clientCert),
                '--cakey=' + str(self.clientauthKey),
                '--keyfile=' + str(self.clientkeyfile)])
        log('Create JWT secrets')
        for node in [self.cluster1, self.cluster2]:
            certOp(['jwt-secret', '--secret=' + str(node["SyncSecret"])])
            certOp(['jwt-secret', '--secret=' + str(node["JWTSecret"])])

        def addStarter(val, port):
            val["instance"] = starterManager(
                self.basecfg,
                val["dir"],    
                port=port, 
                mode='cluster',
                moreopts= ['--starter.sync'
                          ,'--starter.local'
                          ,'--auth.jwt-secret=' +           str(val["JWTSecret"])
                          ,'--sync.server.keyfile=' +       str(val["tlsKeyfile"])
                          ,'--sync.server.client-cafile=' + str(self.clientCert)
                          ,'--sync.master.jwt-secret=' +    str(val["SyncSecret"])
                          ,'--starter.address=' +           self.basecfg.publicip
                ])
        addStarter(self.cluster1, None)
        addStarter(self.cluster2, port=9528)

    def setup(self):
        self.cluster1["instance"].runStarter()
        while not self.cluster1["instance"].isInstanceUp():
            log('.')
            time.sleep(1)
        self.cluster1["instance"].detectLogfiles()
        self.cluster1['smport'] = self.cluster1["instance"].getSyncMasterPort()
        
        print(requests.get('http://'+ self.basecfg.publicip +':' + str(self.cluster1['smport'])))

        self.cluster2["instance"].runStarter()
        while not self.cluster2["instance"].isInstanceUp():
            log('.')
            time.sleep(1)
        self.cluster2["instance"].detectLogfiles()
        self.cluster2['smport'] = self.cluster2["instance"].getSyncMasterPort()
        print(requests.get('http://'+ self.basecfg.publicip +':' + str(self.cluster2['smport'])))

        cmd = ['arangosync', 'configure', 'sync',
               '--master.endpoint=https://'
               + self.basecfg.publicip
               + ':'
               + str(self.cluster1['smport']),
               '--master.keyfile=' + str(self.clientkeyfile),
               '--source.endpoint=https://'
               + self.basecfg.publicip
               + ':'
               + str(self.cluster2['smport']),
               '--master.cacert=' + str(self.cacert),
               '--source.cacert=' + str(self.cacert),
               '--auth.keyfile=' + str(self.clientkeyfile)]
        log(str(cmd))
        self.syncInstance = psutil.Popen(cmd)

    def run(self):
        log('Check status of cluster 1')
        self.checkSync=psutil.Popen(['arangosync', 'get', 'status',
                                     '--master.cacert=' + str(self.cacert),
                                     '--master.endpoint=https://' + self.basecfg.publicip + ':' + str(self.cluster1['smport']),
                                     '--auth.keyfile=' + str(self.clientkeyfile),
                                     '--verbose']).wait()

        log('Check status of cluster 2')
        self.checkSync=psutil.Popen(['arangosync', 'get', 'status',
                                     '--master.cacert=' + str(self.cacert),
                                     '--master.endpoint=https://' + self.basecfg.publicip + ':' + str(self.cluster2['smport']),
                                     '--auth.keyfile=' + str(self.clientkeyfile),
                                     '--verbose']).wait()

    def postSetup(self):
        pass
    def jamAttempt(self):
        pass
    def shutdown(self):
        self.syncInstance.terminate()
        self.syncInstance.wait(timeout=60)
        self.cluster1["instance"].killInstance()
        self.cluster2["instance"].killInstance()

def get(typeof, baseconfig):
    print("get!")
    if typeof == runnertype.LEADER_FOLLOWER:
        return LeaderFollower(baseconfig)
        
    if typeof == runnertype.ACTIVE_FAILOVER:
        return activeFailover(baseconfig)
        
    if typeof == runnertype.CLUSTER:
        return cluster(baseconfig)
        
    if typeof == runnertype.DC2DC:
        return dc2dc(baseconfig)
    raise Exception("unknown starter type")
