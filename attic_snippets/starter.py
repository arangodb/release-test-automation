
import time
import os
import sys
import re
import requests
import subprocess
Popen=subprocess.Popen

class arangoshExecutor(object):
    def __init__(self, username, port, passvoid="", jwt=None):
        self.username = username
        self.passvoid = passvoid
        self.jwtfile = jwt
        self.port = port

    def runCommand(self, command):
        cmd = ["/usr/bin/arangosh",
               "--server.endpoint", "tcp://127.0.0.1:%d" %(int(self.port)),
               "--server.username", "%s" % (self.username),
               "--server.password", "%s" % (self.passvoid),
               "--javascript.execute-string", "%s" % (command)]

        print(cmd)
        PIPE=subprocess.PIPE
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
    def __init__(self, basedir, mode, port=None, moreopts = []):
        self.basedir = basedir
        self.logfileName = basedir + "/arangodb.log"
        self.port = port
        self.username = 'root'
        self.passvoid = ''
        self.mode = mode
        self.isMaster = None
        self.isLeader = False
        self.arangoshExecutor = None
        self.frontendPort = None
        self.allInstances = []
        self.executor = None
        if self.port != None:
            self.frontendPort = port + 1
            moreopts += ["--starter.port", "%d" % port]
        self.arguments = ["/usr/bin/arangodb",
                          "--log.console=false",
                          "--log.file=true",
                          "--starter.data-dir=%s" % self.basedir,
                          "--starter.mode",
                          self.mode ] + moreopts
        self.instance = Popen(self.arguments)
        time.sleep(1)

    def executeFrontend(self, cmd):
        if self.arangoshExecutor == None:
            self.arangoshExecutor = arangoshExecutor(username="root", port=int(self.frontendPort), passvoid="")
        return self.arangoshExecutor.runCommand(command=cmd)

    def killInstance(self):
        print("Killing: " + str(self.arguments))
        self.instance.terminate()
        print(self.instance.wait(timeout=30))
        print("Instance now dead.")
        
    def respawnInstance(self):
        print("respawning instance")
        self.instance = Popen(self.arguments)
        time.sleep(2)        
        
    def getFrontendPort(self):
        if self.frontendPort == None:
            raise Exception("no frontend port detected")
        return self.frontendPort

    def getLogFile(self):
        return open(self.logfileName).read()

    def isInstanceUp(self):
        print(self.instance.poll())
        if self.instance.poll() != None:
            raise Exception("my instance is gone! " + self.basedir)
        lf = self.getLogFile()
        rx = re.compile('(\w*) up and running ')
        for line in lf.splitlines():
            m = rx.search(line)
            if m == None:
                continue
            g = m.groups()
            if len(g) == 1 and g[0] == 'agent':
                print('agent')
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
                print(self.allInstances)

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
        print(self.instance.poll())
        if self.instance.poll() != None:
            raise Exception("my instance is gone! " + self.basedir)
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
            raise Exception("Unable to get my host state! " + self.basedir + " - " + lf)
        self.frontendPort = m.groups()[0]
    def ActiveFailoverDetectHostNowFollower(self):
        if self.instance.poll() != None:
            raise Exception("my instance is gone! " + self.basedir)
        lf = self.getLogFile()
        if lf.find('resilientsingle up and running as follower') >= 0:
            self.isMaster = False
            return True
        return False

def activeFailover():
    print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    print("xx           Active Failover Test      ")
    print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    instances = []
    print("launching 0")
    instances.append(starterManager('/tmp/AFO/node1', mode='activefailover'))
    print("launching 1")
    instances.append(starterManager('/tmp/AFO/node2', mode='activefailover', moreopts=['--starter.join', '127.0.0.1'] ))
    print("launching 2")
    instances.append(starterManager('/tmp/AFO/node3', mode='activefailover', moreopts=['--starter.join','127.0.0.1']))
    print("waiting for the instances to become alive")
    while not instances[0].isInstanceUp() and not instances[1].isInstanceUp() and not instances[1].isInstanceUp():
        print('.')
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
        if not node.isLeader:
            followerNodes.append(node)
    print("system ready, starting test")
    success = True
    r = requests.get('http://127.0.0.1:' + leader.getFrontendPort())
    print(r)
    if r.status_code != 200:
        print(r.text)
        success = False
    print('http://127.0.0.1:' + followerNodes[0].getFrontendPort())
    r = requests.get('http://127.0.0.1:' + followerNodes[0].getFrontendPort())
    print(r)
    print(r.text)
    if r.status_code != 503:
        success = False
    print('http://127.0.0.1:' + followerNodes[1].getFrontendPort())
    r = requests.get('http://127.0.0.1:' + followerNodes[1].getFrontendPort())
    print(r)
    print(r.text)
    if r.status_code != 503:
        success = False
    print(success)
    print('leader can be reached at: ' + 'http://35.246.150.144:' + leader.getFrontendPort())
    input("Press Enter to continue...")
    leader.killInstance()
    print("waiting for new leader...")
    newLeader = None
    while newLeader == None:
        for node in followerNodes:
            node.detectLeader()
            if node.isLeader:
                print('have a new leader: ' + str(node.arguments))
                newLeader = node;
                break
            print('.')
        time.sleep(1)
    print(newLeader)
    r = requests.get('http://127.0.0.1:' + newLeader.getFrontendPort() + '/_db/_system/_admin/aardvark/index.html#replication')
    print(r)
    if r.status_code != 200:
        print(r.text)
        success = False
    print('new leader can be reached at: ' + 'http://35.246.150.144:' + newLeader.getFrontendPort())
    input("Press Enter to continue...")
    
    leader.respawnInstance()

    print("waiting for old leader to show up as follower")
    while not leader.ActiveFailoverDetectHostNowFollower():
        print('.')
        time.sleep(1)
    print("Now is follower")
    r = requests.get('http://127.0.0.1:' + leader.getFrontendPort())
    print(r)
    print(r.text)
    if r.status_code != 503:
        success = False
    print("state of this test is: " + "Success" if success else "Failed")
    input("Press Enter to finish this test")
    for node in instances:
        node.killInstance()
    print('test ended')

def cluster():
    print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    print("xx           Cluster Test      ")
    print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    instances = []
    jwtfile = '/tmp/secret'
    f = open(jwtfile, 'w')
    f.write(str(time.clock()))
    f.close()
    print("launching 0")
    instances.append(starterManager('/tmp/cluster/node1', mode='cluster', moreopts=['--auth.jwt-secret', jwtfile]))
    print("launching 1")
    instances.append(starterManager('/tmp/cluster/node2', mode='cluster', moreopts=['--auth.jwt-secret', jwtfile, '--starter.join', '127.0.0.1']))
    print("launching 2")
    instances.append(starterManager('/tmp/cluster/node3', mode='cluster', moreopts=['--auth.jwt-secret', jwtfile, '--starter.join', '127.0.0.1']))
    print("waiting for the instances to become alive")
    while not instances[0].isInstanceUp() and not instances[1].isInstanceUp() and not instances[1].isInstanceUp():
        print('.')
        time.sleep(1)
    for node in instances:
        node.detectLogfiles()
        print('coordinator can be reached at: ' + 'http://35.246.150.144:' + node.getFrontendPort())

    print('Starting instance without jwt')
    deadInstance = starterManager('/tmp/cluster/nodeX', mode='cluster', moreopts=['--starter.join', '127.0.0.1'])
    print(deadInstance.instance.wait(timeout=120))
    print('dead instance is dead?')

    instances[0].executeFrontend("""
db._create("testCollection",  { numberOfShards: 6, replicationFactor: 2});
db.testCollection.save({test: "document"})
""")
    input("Press Enter to continue")

    print("stopping instance 2")
    instances[2].killInstance()
    input("Press Enter to continue")

    instances[2].respawnInstance()
    
    input("Press Enter to finish this test")
    for node in instances:
        node.killInstance()
    print('test ended')
        
def LeaderFollower():
    print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    print("xx           Leader Follower Test      ")
    print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    print("launching Leader")
    leader = starterManager('/tmp/lf/leader', mode='single', port=1234)
    print("launching Follower")
    follower = starterManager('/tmp/lf/follower', mode='single', port=2345)
    print(leader.port)
    leaderArangosh = arangoshExecutor(username=leader.username, passvoid=leader.passvoid, port=leader.frontendPort)
    followerArangosh = arangoshExecutor(username=follower.username, passvoid=follower.passvoid, port=follower.frontendPort)
    print("waiting for the instances to become alive")
    while not leader.isInstanceUp() and not follower.isInstanceUp():
        print('.')
        time.sleep(1)

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

    print("creating a document...")
    print(leaderArangosh.runCommand(beforeReplJS))
    print("launching replication")
    print(followerArangosh.runCommand(startReplJS))
    print("creating some more documents...")
    print(leaderArangosh.runCommand(afterReplJS))

    print("checking for the replication")

    count = 0
    while count < 300:
        if followerArangosh.runCommand(checkReplJS) == 0:
            break
        print(".")
        time.sleep(1)
        count += 1
    if (count > 29):
        raise Exception("replication didn't make it in 30s!")
    print("all OK!")
    input("Press Enter to finish this test")
    leader.killInstance()
    follower.killInstance()
    print('test ended')

#LeaderFollower()
activeFailover()
cluster()
