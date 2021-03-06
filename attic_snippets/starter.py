import datetime
import time
import os
import sys
import re
import requests
import subprocess
import signal
import psutil
Popen=psutil.Popen
def timestamp():
    return datetime.datetime.utcnow().isoformat()
def log(string):
    print(timestamp() + " " + string)

basebindirectory = "c:/Programme/ArangoDB3e 3.6.2/"
basetestdatadir = "c:/tmp/"
#
os.chdir(basebindirectory)
# import miniupnpc
#u = miniupnpc.UPnP()
#u.discoverdelay = 200
#u.discover()
#u.selectigd()
#print('external ip address: {}'.format(u.externalipaddress()))
IP='192.168.173.88'
      
class arangoshExecutor(object):
    def __init__(self, username, port8529, passvoid="", jwt=None):
        self.username = username
        self.passvoid = passvoid
        self.jwtfile = jwt
        self.port = port

    def runCommand(self, command, description):
        cmd = [basebindirectory + "usr/bin/arangosh",
               "--server.endpoint", "tcp://127.0.0.1:%d" %(int(self.port)),
               "--server.username", "%s" % (self.username),
               "--server.password", "%s" % (self.passvoid),
               "--javascript.execute-string", "%s" % (command)]

        log("launching " + description)
        # PIPE=subprocess.PIPE
        Popen=psutil.Popen
        log(str(cmd))
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
    def __init__(self, basedir, mode, port=None, jwtStr=None, moreopts=[]):
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
        if jwtStr != None:
            print("JWT!")
            os.makedirs(self.basedir)
            jwtfile = os.path.join(self.basedir, 'jwt')
            f = open(jwtfile, 'w')
            f.write(jwtStr)
            f.close()
            self.moreopts = ['--auth.jwt-secret', jwtfile] + self.moreopts
        if self.port != None:
            self.frontendPort = port + 1
            self.moreopts += ["--starter.port", "%d" % port]
        self.arguments = [basebindirectory + "usr/bin/arangodb",
                          "--log.console=false",
                          "--log.file=true",
                          "--starter.data-dir=%s" % self.basedir,
                          "--starter.mode", self.mode
        ] + self.moreopts
        log("launching " + str(self.arguments))
        self.instance = Popen(self.arguments)
        time.sleep(self.startupwait)

    def executeFrontend(self, cmd, description):
        if self.arangoshExecutor == None:
            self.arangoshExecutor = arangoshExecutor(username="root", port=int(self.frontendPort), passvoid="")
        return self.arangoshExecutor.runCommand(command=cmd, description=description)

    def killInstance(self):
        log("Killing: " + str(self.arguments))
        self.instance.send_signal(signal.CTRL_C_EVENT)
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

    def isInstanceRunning(self):
        return self.instance.is_running()
                          
    def isInstanceUp(self):
        if not self.instance.is_running():
            print(self.instance)
            print(self.instance.status())
            print(dir(self.instance))
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
        if not self.instance.is_running():
            print(self.instance)
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
        if not self.instance.is_running():
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
    instances.append(starterManager(basetestdatadir + 'AFO/node1', mode='activefailover', moreopts=[]))
    log("launching 1")
    instances.append(starterManager(basetestdatadir + 'AFO/node2', mode='activefailover', moreopts=['--starter.join', '127.0.0.1'] ))
    log("launching 2")
    instances.append(starterManager(basetestdatadir + 'AFO/node3', mode='activefailover', moreopts=['--starter.join','127.0.0.1']))
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
    log('leader can be reached at: ' + 'http://' + IP + ':' + leader.getFrontendPort())
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
    log('new leader can be reached at: ' + 'http://' + IP + ':' + newLeader.getFrontendPort())
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
    jwtdatastr = str(timestamp())
    log("launching 0")
    instances.append(starterManager(basetestdatadir + 'cluster/node1', mode='cluster', jwtStr=jwtdatastr, moreopts=[]))
    log("launching 1")
    instances.append(starterManager(basetestdatadir + 'cluster/node2', mode='cluster', jwtStr=jwtdatastr, moreopts=['--starter.join', '127.0.0.1']))
    log("launching 2")
    instances.append(starterManager(basetestdatadir + 'cluster/node3', mode='cluster', jwtStr=jwtdatastr, moreopts=['--starter.join', '127.0.0.1']))
    log("waiting for the instances to become alive")
    while not instances[0].isInstanceUp() and not instances[1].isInstanceUp() and not instances[1].isInstanceUp():
        log('.')
        time.sleep(1)
    for node in instances:
        node.detectLogfiles()
        node.detectInstancePIDs()
        log('coordinator can be reached at: ' + 'http://' + IP + ':' + node.getFrontendPort())

    #log('Starting instance without jwt')
    #deadInstance = starterManager(basetestdatadir + 'cluster/nodeX', mode='cluster', jwtStr=None, moreopts=['--starter.join', '127.0.0.1'])
    #i = 0
    #while True:
    #    log("." + str(i))
    #    if not deadInstance.isInstanceRunning():
    #        break
    #    if i > 30:
    #        log('Giving up wating for the starter to exit')
    #        raise Exception("non-jwt-ed starter won't exit")
    #    i += 1
    #    time.sleep(10)
    #log(str(deadInstance.instance.wait(timeout=320)))
    #log('dead instance is dead?')

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
    leader = starterManager(basetestdatadir + 'lf/leader', mode='single', port=1234, moreopts=[])
    log("launching Follower")
    follower = starterManager(basetestdatadir + 'lf/follower', mode='single', port=2345, moreopts=[])
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

def dc2dc():
    def Popen(cmds):
        print(cmds)
        return psutil.Popen(cmds)
    certificateDir = os.path.join(basetestdatadir, "dc2dc", "certs")
    dataDir = os.path.join(basetestdatadir, "dc2dc", "data")
    os.makedirs(certificateDir)
    os.makedirs(dataDir)
    arangodbBin = basebindirectory + 'usr/bin/arangodb'
    log('Create TLS certificates')
    Popen([arangodbBin, 'create', 'tls', 'ca',
           '--cert=' + certificateDir + '/tls-ca.crt',
           '--key=' + certificateDir + '/tls-ca.key']).wait()
    Popen([arangodbBin, 'create', 'tls', 'keyfile'
           '--cacert=' + certificateDir + '/tls-ca.crt',
           '--cakey=' + certificateDir + '/tls-ca.key',
           '--keyfile=' + certificateDir + '/cluster1/tls.keyfile',
           '--host=' + IP, '--host=localhost']).wait()
    Popen([arangodbBin, 'create', 'tls', 'keyfile',
           '--cacert=' + certificateDir + '/tls-ca.crt',
           '--cakey=' + certificateDir + '/tls-ca.key',
           '--keyfile=' + certificateDir + '/cluster2/tls.keyfile',
           '--host=' + IP, '--host=localhost']).wait()
    log('Create client authentication certificates')
    Popen([arangodbBin, 'create', 'client-auth', 'ca',
           '--cert=' + certificateDir + '/client-auth-ca.crt',
           '--key=' + certificateDir + '/client-auth-ca.key']).wait()
    Popen([arangodbBin, 'create', 'client-auth', 'keyfile',
           '--cacert=' + certificateDir + '/client-auth-ca.crt',
           '--cakey=' + certificateDir + '/client-auth-ca.key',
           '--keyfile=' + certificateDir + '/client-auth-ca.keyfile']).wait()
    log('Create JWT secrets')
    Popen([arangodbBin, 'create', 'jwt-secret', '--secret=' + certificateDir + '/cluster1/syncmaster.jwtsecret']).wait()
    Popen([arangodbBin, 'create', 'jwt-secret', '--secret=' + certificateDir + '/cluster1/arangodb.jwtsecret']).wait()
    Popen([arangodbBin, 'create', 'jwt-secret', '--secret=' + certificateDir + '/cluster2/syncmaster.jwtsecret']).wait()
    Popen([arangodbBin, 'create', 'jwt-secret', '--secret=' + certificateDir + '/cluster2/arangodb.jwtsecret']).wait()

    log('starting first cluster')
    firstCluster=starterManager(basedir=dataDir + '/cluster1', mode='cluster', moreopts=[
        '--starter.sync',
        '--starter.local',
        '--auth.jwt-secret=' + certificateDir + '/cluster1/arangodb.jwtsecret',
        '--sync.server.keyfile=' + certificateDir + '/cluster1/tls.keyfile',
        '--sync.server.client-cafile=' + certificateDir + '/client-auth-ca.crt',
        '--sync.master.jwt-secret=' + certificateDir + '/cluster1/syncmaster.jwtsecret',
        '--starter.address=' + IP])
    time.sleep(20)
    print(requests.get('http://'+IP+':8542'))
    secondCluster=starterManager(basedir=dataDir + '/cluster2', mode='cluster', port=9528, moreopts=[
        '--starter.sync',
        '--starter.local',
        '--auth.jwt-secret=' + certificateDir + '/cluster2/arangodb.jwtsecret',
        '--sync.server.keyfile=' + certificateDir + '/cluster2/tls.keyfile',
        '--sync.server.client-cafile=' + certificateDir + '/client-auth-ca.crt',
        '--sync.master.jwt-secret=' + certificateDir + '/cluster2/syncmaster.jwtsecret',
        '--starter.address=' + IP])
    log('waiting')
    print(requests.get('http://'+IP+':8542'))
    time.sleep(20)# todo!
    print(requests.get('http://'+IP+':9542'))
    print(requests.get('http://'+IP+':8542'))

    syncInstance = Popen(['arangosync', 'configure', 'sync',
                          '--master.endpoint=https://' + IP + ':9542',
                          '--master.keyfile=' + certificateDir + '/client-auth-ca.keyfile',
                          '--source.endpoint=https://' + IP + ':8542',
                          '--master.cacert=' + certificateDir + '/tls-ca.crt',
                          '--source.cacert=' + certificateDir + '/tls-ca.crt',
                          '--auth.keyfile=' + certificateDir + '/client-auth-ca.keyfile'])
    log('Check status of cluster 1')
    checkSync=Popen(['arangosync', 'get', 'status',
                     '--master.cacert=' + certificateDir + '/tls-ca.crt',
                     '--master.endpoint=https://' + IP + ':8542',
                     '--auth.keyfile=' + certificateDir + '/client-auth-ca.keyfile',
                     '--verbose']).wait()

    log('Check status of cluster 2')
    checkSync2=Popen(['arangosync', 'get', 'status',
                      '--master.cacert=' + certificateDir + '/tls-ca.crt',
                      '--master.endpoint=https://' + IP + ':9542',
                      '--auth.keyfile=' + certificateDir + '/client-auth-ca.keyfile',
                      '--verbose']).wait()

#dc2dc()
#LeaderFollower()
#activeFailover()
cluster()
