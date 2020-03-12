import datetime
import time
import os
import sys
import re
import requests
import subprocess
Popen=subprocess.Popen
def timestamp():
    return datetime.datetime.utcnow().isoformat()
def log(string):
    print(timestamp() + " " + string)

import miniupnpc

u = miniupnpc.UPnP()
u.discoverdelay = 200
u.discover()
u.selectigd()
print('external ip address: {}'.format(u.externalipaddress()))
      
class arangoshExecutor(object):
    def __init__(self, username, port, passvoid="", jwt=None):
        self.username = username
        self.passvoid = passvoid
        self.jwtfile = jwt
        self.port = port

    def runCommand(self, command, description):
        cmd = ["/usr/bin/arangosh",
               "--server.endpoint", "tcp://127.0.0.1:%d" %(int(self.port)),
               "--server.username", "%s" % (self.username),
               "--server.password", "%s" % (self.passvoid),
               "--javascript.execute-string", "%s" % (command)]

        log("launching " + description)
        # PIPE=subprocess.PIPE
        Popen=subprocess.Popen
        p = Popen(cmd)#, stdout=PIPE, stdin=PIPE, stderr=PIPE, universal_newlines=True)
        # print('l')
        # l = p.stdout.read()
        # print(l)
        # print('p')
        # e = p.stderr.read()
        # print(p)
        # print('wait')
        return p.wait(timeout=30)
        

class starterManager(object):
    def __init__(self, basedir, mode, port=None, moreopts=[]):
        self.basedir = basedir
        self.logfileName = basedir + "/arangodb.log"
        self.port = port
        self.startupwait = 1
        self.username = 'root'
        self.passvoid = ''
        self.mode = mode
        self.isMaster = None
        self.isLeader = False
        self.arangoshExecutor = None
        self.frontendPort = None
        self.allInstances = []
        self.executor = None
        self.moreopts = moreopts
        if self.port != None:
            self.frontendPort = port + 1
            self.moreopts += ["--starter.port", "%d" % port]
        self.arguments = ["/usr/bin/arangodb",
                          "--log.console=false",
                          "--log.file=true",
                          "--starter.data-dir=%s" % self.basedir,
                          "--starter.mode",
                          self.mode ] + self.moreopts
        log("launching " + str(self.arguments))
        self.instance = Popen(self.arguments)
        time.sleep(self.startupwait)

    def executeFrontend(self, cmd, description):
        if self.arangoshExecutor == None:
            self.arangoshExecutor = arangoshExecutor(username="root", port=int(self.frontendPort), passvoid="")
        return self.arangoshExecutor.runCommand(command=cmd, description=description)

    def killInstance(self):
        log("Killing: " + str(self.arguments))
        self.instance.terminate()
        log(str(self.instance.wait(timeout=30)))
        log("Instance now dead.")
        
    def respawnInstance(self):
        log("respawning instance " + str(self.arguments))
        self.instance = Popen(self.arguments)
        time.sleep(self.startupwait)
        
    def getFrontendPort(self):
        if self.frontendPort == None:
            raise Exception(timestamp() + "no frontend port detected")
        return self.frontendPort

    def getLogFile(self):
        return open(self.logfileName).read()

    def isInstanceUp(self):
        if self.instance.poll() != None:
            raise Exception(timestamp() + "my instance is gone! " + self.basedir)
        lf = self.getLogFile()
        rx = re.compile('(\w*) up and running ')
        for line in lf.splitlines():
            m = rx.search(line)
            if m == None:
                continue
            g = m.groups()
            if len(g) == 1 and g[0] == 'agent':
                continue
            return True
        return False

    def detectLogfiles(self):
        for one in os.listdir(self.basedir):
            if os.path.isdir(os.path.join(self.basedir, one)):
                m = re.match(r'([a-z]*)(\d*)', one)
                instance = {
                    'type': m.group(1),
                    'port': m.group(2),
                    'logfile': os.path.join(self.basedir, one, 'arangod.log')
                    }
                if instance['type'] == 'agent':
                    self.agentInstance = instance
                elif instance['type'] == 'coordinator':
                    self.coordinator = instance
                    self.frontendPort = instance['port']
                elif instance['type'] == 'resilientsingle':
                    self.dbInstance = instance
                    self.frontendPort = instance['port']
                else:
                    self.dbInstance = instance
                self.allInstances.append(instance)
        log(str(self.allInstances))

    def detectInstancePIDs(self):
        for instance in self.allInstances:
            instance['PID'] = 0
            while instance['PID'] == 0:
                lf = open(self.dbInstance['logfile']).read()
                pos = lf.find('is ready for business.')
                if pos < 0:
                    log('.')
                    time.sleep(1)
                    continue
                pos = lf.rfind('\n', 0, pos)
                epos = lf.find('\n', pos + 1, len(lf))
                log(str(pos))
                log(str(epos))
                line = lf[pos: epos]
                m = re.search(r'Z \[(\d*)\]', line)
                if m == None:
                    raise Exception(timestamp() + " Couldn't find a PID in hello line! - " + line)
                instance['PID'] = int(m.groups()[0])
        log(str(self.allInstances))

    def detectLeader(self):
        lf = self.readInstanceLogfile()
        self.isLeader = ((lf.find('Became leader in') >= 0) or
                         (lf.find('Successful leadership takeover: All your base are belong to us') >= 0))
        return self.isLeader
    
    def readInstanceLogfile(self):
        return open(self.dbInstance['logfile']).read()

    def readAgentLogfile(self):
        return open(self.agent['logfile']).read()
    
    def ActiveFailoverDetectHosts(self):
        if self.instance.poll() != None:
            raise Exception(timestamp() + "my instance is gone! " + self.basedir)
        # this is the way to detect the master starter...
        lf = self.getLogFile()
        if lf.find('Just became master') >= 0:
            self.isMaster = True
        else:
            self.isMaster = False
        rx = re.compile('Starting resilientsingle on port (\d*) .*')
        m = rx.search(lf)
        if m == None:
            print(rx)
            print(m)
            raise Exception(timestamp() + "Unable to get my host state! " + self.basedir + " - " + lf)
        self.frontendPort = m.groups()[0]
    def ActiveFailoverDetectHostNowFollower(self):
        if self.instance.poll() != None:
            raise Exception(timestamp() + "my instance is gone! " + self.basedir)
        lf = self.getLogFile()
        if lf.find('resilientsingle up and running as follower') >= 0:
            self.isMaster = False
            return True
        return False

def activeFailover():
    log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    log("xx           Active Failover Test      ")
    log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    instances = []
    log("launching 0")
    instances.append(starterManager('/tmp/AFO/node1', mode='activefailover'))
    log("launching 1")
    instances.append(starterManager('/tmp/AFO/node2', mode='activefailover', moreopts=['--starter.join', '127.0.0.1'] ))
    log("launching 2")
    instances.append(starterManager('/tmp/AFO/node3', mode='activefailover', moreopts=['--starter.join','127.0.0.1']))
    log("waiting for the instances to become alive")
    while not instances[0].isInstanceUp() and not instances[1].isInstanceUp() and not instances[1].isInstanceUp():
        log('.')
        time.sleep(1)
    for node in instances:
        node.detectLogfiles()
        node.ActiveFailoverDetectHosts()
    leader = None
    followerNodes = []
    while leader == None:
        for node in instances:
            if node.detectLeader():
                leader = node
                break
    for node in instances:
        node.detectInstancePIDs()
        if not node.isLeader:
            followerNodes.append(node)
    log("system ready, starting test")
    success = True
    r = requests.get('http://127.0.0.1:' + leader.getFrontendPort())
    log(str(r))
    if r.status_code != 200:
        log(r.text)
        success = False
    log('http://127.0.0.1:' + followerNodes[0].getFrontendPort())
    r = requests.get('http://127.0.0.1:' + followerNodes[0].getFrontendPort())
    log(str(r))
    log(r.text)
    if r.status_code != 503:
        success = False
    log('http://127.0.0.1:' + followerNodes[1].getFrontendPort())
    r = requests.get('http://127.0.0.1:' + followerNodes[1].getFrontendPort())
    log(str(r))
    log(r.text)
    if r.status_code != 503:
        success = False
    log("success" if success else "fail")
    log('leader can be reached at: ' + 'http://35.246.150.144:' + leader.getFrontendPort())
    input("Press Enter to continue...")
    leader.killInstance()
    log("waiting for new leader...")
    newLeader = None
    while newLeader == None:
        for node in followerNodes:
            node.detectLeader()
            if node.isLeader:
                log('have a new leader: ' + str(node.arguments))
                newLeader = node;
                break
            log('.')
        time.sleep(1)
    log(str(newLeader))
    r = requests.get('http://127.0.0.1:' + newLeader.getFrontendPort() + '/_db/_system/_admin/aardvark/index.html#replication')
    log(str(r))
    if r.status_code != 200:
        log(r.text)
        success = False
    log('new leader can be reached at: ' + 'http://35.246.150.144:' + newLeader.getFrontendPort())
    input("Press Enter to continue...")
    
    leader.respawnInstance()

    log("waiting for old leader to show up as follower")
    while not leader.ActiveFailoverDetectHostNowFollower():
        log('.')
        time.sleep(1)
    log("Now is follower")
    r = requests.get('http://127.0.0.1:' + leader.getFrontendPort())
    log(str(r))
    log(r.text)
    if r.status_code != 503:
        success = False
    log("state of this test is: " + "Success" if success else "Failed")
    input("Press Enter to finish this test")
    for node in instances:
        node.killInstance()
    log('test ended')

def cluster():
    log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    log("xx           Cluster Test      ")
    log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    instances = []
    jwtfile = '/tmp/secret'
    f = open(jwtfile, 'w')
    f.write(str(time.clock()))
    f.close()
    log("launching 0")
    instances.append(starterManager('/tmp/cluster/node1', mode='cluster', moreopts=['--auth.jwt-secret', jwtfile]))
    log("launching 1")
    instances.append(starterManager('/tmp/cluster/node2', mode='cluster', moreopts=['--auth.jwt-secret', jwtfile, '--starter.join', '127.0.0.1']))
    log("launching 2")
    instances.append(starterManager('/tmp/cluster/node3', mode='cluster', moreopts=['--auth.jwt-secret', jwtfile, '--starter.join', '127.0.0.1']))
    log("waiting for the instances to become alive")
    while not instances[0].isInstanceUp() and not instances[1].isInstanceUp() and not instances[1].isInstanceUp():
        log('.')
        time.sleep(1)
    for node in instances:
        node.detectLogfiles()
        node.detectInstancePIDs()
        log('coordinator can be reached at: ' + 'http://35.246.150.144:' + node.getFrontendPort())

    log('Starting instance without jwt')
    deadInstance = starterManager('/tmp/cluster/nodeX', mode='cluster', moreopts=['--starter.join', '127.0.0.1'])
    log(str(deadInstance.instance.wait(timeout=120)))
    log('dead instance is dead?')

    instances[0].executeFrontend("""
db._create("testCollection",  { numberOfShards: 6, replicationFactor: 2});
db.testCollection.save({test: "document"})
""",
                                 "create test collection")
    input("Press Enter to continue")

    log("stopping instance 2")
    instances[2].killInstance()
    input("Press Enter to continue")

    instances[2].respawnInstance()
    
    input("Press Enter to finish this test")
    for node in instances:
        node.killInstance()
    log('test ended')

def LeaderFollower():
    log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    log("xx           Leader Follower Test      ")
    log("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    log("launching Leader")
    leader = starterManager('/tmp/lf/leader', mode='single', port=1234)
    log("launching Follower")
    follower = starterManager('/tmp/lf/follower', mode='single', port=2345)
    leaderArangosh = arangoshExecutor(username=leader.username, passvoid=leader.passvoid, port=leader.frontendPort)
    followerArangosh = arangoshExecutor(username=follower.username, passvoid=follower.passvoid, port=follower.frontendPort)
    log("waiting for the instances to become alive")
    while not leader.isInstanceUp() and not follower.isInstanceUp():
        log('.')
        time.sleep(1)
    leader.detectLogfiles()
    leader.detectInstancePIDs()
    follower.detectLogfiles()
    follower.detectInstancePIDs()

    startReplJS = """
require("@arangodb/replication").setupReplicationGlobal({
    endpoint: "tcp://127.0.0.1:%d",
    username: "root",
    password: "",
    verbose: false,
    includeSystem: true,
    incremental: true,
    autoResync: true
    });
""" % (leader.port + 1)

    beforeReplJS = """
db._create("testCollectionBefore");
db.testCollectionBefore.save({"hello": "world"})
"""
    afterReplJS =  """
db._create("testCollectionAfter");
db.testCollectionAfter.save({"hello": "world"})
"""
    checkReplJS = """
if (!db.testCollectionBefore.toArray()[0]["hello"] === "world") {
  throw new Error("before not yet there?");
}
if (!db.testCollectionAfter.toArray()[0]["hello"] === "world") {
  throw new Error("after not yet there?");
}
"""

    log(str(leaderArangosh.runCommand(beforeReplJS, "creating data before starting the replication")))
    log(str(followerArangosh.runCommand(startReplJS, "launching replication")))
    log(str(leaderArangosh.runCommand(afterReplJS, "creating some more documents...")))

    log("checking for the replication")

    count = 0
    while count < 300:
        if followerArangosh.runCommand(checkReplJS, "checking replication state") == 0:
            break
        log(".")
        time.sleep(1)
        count += 1
    if (count > 29):
        raise Exception("replication didn't make it in 30s!")
    log("all OK!")
    input("Press Enter to finish this test")
    leader.killInstance()
    follower.killInstance()
    log('test ended')

LeaderFollower()
input("Press Enter to continue")
activeFailover()
cluster()
