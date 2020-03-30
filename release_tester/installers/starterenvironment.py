import time
from logging import info as log
from enum import Enum
from pathlib import Path
from abc import abstractmethod
from startermanager import starterManager
from installers.arangosh import arangoshExecutor

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
    def setup(self):
        pass
    def run(self):
        pass
    def postSetup(self):
        pass
    def jamAttempt(self):
        pass
    def shutdown(self):
        pass




class cluster(runner):
    def __init__(self, cfg):
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        log("xx           cluster test      ")
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.basecfg = cfg
    def setup(self):
        pass
    def run(self):
        pass
    def postSetup(self):
        pass
    def jamAttempt(self):
        pass
    def shutdown(self):
        pass

class dc2dc(runner):
    def __init__(self, cfg):
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        log("xx           dc 2 dc test      ")
        log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self.basecfg = cfg
    def setup(self):
        pass
    def run(self):
        pass
    def postSetup(self):
        pass
    def jamAttempt(self):
        pass
    def shutdown(self):
        pass


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
