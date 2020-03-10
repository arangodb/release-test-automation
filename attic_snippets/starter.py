import time
import pexpect
import os
import sys
import re
import requests

class starterManager(object):
    def __init__(self, basedir, mode, port=None, moreopts = ""):
        self.basedir = basedir
        self.logfileName = basedir + "/arangodb.log"
        self.port = port
        self.username = 'root'
        self.passvoid = ''
        self.mode = mode
        self.isMaster = None
        self.frontendPort = None
        if self.port != None:
            self.frontendPort = port + 1
            moreopts += " --starter.port %d" % port
        self.arguments = "arangodb --log.console=false --log.file=true --starter.data-dir=%s --starter.mode %s %s" % (
            self.basedir,
            self.mode,
            moreopts)
        self.instance = pexpect.spawnu(self.arguments)
        time.sleep(2)

    def killInstance(self):
        print("Killing: " + self.arguments)
        self.instance.kill(15)
        self.instance.expect(pexpect.EOF, timeout=30)
        while self.instance.isalive():
            print('.')
        print("Instance now dead.")
        
    def respawnInstance(self):
        print("respawning instance")
        self.instance = pexpect.spawnu(self.arguments)
        time.sleep(2)        
        
    def getFrontendPort(self):
        if self.frontendPort == None:
            raise Exception("no frontend port detected")
        return self.frontendPort

    def getLogFile(self):
        return open(self.logfileName).read()

    def isInstanceUp(self):
        if not self.instance.isalive():
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
    def ActiveFailoverDetectHosts(self):
        if not self.instance.isalive():
            raise Exception("my instance is gone! " + self.basedir)
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
        if not self.instance.isalive():
            raise Exception("my instance is gone! " + self.basedir)
        lf = self.getLogFile()
        if lf.find('resilientsingle up and running as follower') >= 0:
            self.isMaster = False
            return True
        return False

def activeFailover():
    instances = []
    print("launching 0")
    instances.append(starterManager('/tmp/AFO/node1', mode='activefailover'))
    print("launching 1")
    instances.append(starterManager('/tmp/AFO/node2', mode='activefailover', moreopts='--starter.join 127.0.0.1' ))
    print("launching 2")
    instances.append(starterManager('/tmp/AFO/node3', mode='activefailover', moreopts='--starter.join 127.0.0.1'))
    print("waiting for the instances to become alive")
    while not instances[0].isInstanceUp() and not instances[1].isInstanceUp() and not instances[1].isInstanceUp():
        print('.')
        time.sleep(1)
    master = None
    followerNodes = []
    for node in instances:
        node.ActiveFailoverDetectHosts()
        if node.isMaster:
            master = node
        else:
            followerNodes.append(node)
    success = True
    r = requests.get('http://127.0.0.1:' + master.getFrontendPort())
    print(r)
    if r.status_code != 200:
        print(r.text)
        success = False
    r = requests.get('http://127.0.0.1:' + followerNodes[0].getFrontendPort())
    print(r)
    print(r.text)
    if r.status_code != 503:
        success = False
    r = requests.get('http://127.0.0.1:' + followerNodes[1].getFrontendPort())
    print(r)
    print(r.text)
    if r.status_code != 503:
        success = False
    print(success)
    print(dir(master))

    master.killInstance()
    print("waiting for new master...")
    newMaster = None
    while newMaster == None:
        for node in followerNodes:
            node.ActiveFailoverDetectHosts()
            if node.isMaster:
                print('have a new master: ' + node.arguments)
                newMaster = node;
                break
            print('.')
        time.sleep(1)
    print(newMaster)
    r = requests.get('http://127.0.0.1:' + newMaster.getFrontendPort())
    print(r)
    if r.status_code != 200:
        print(r.text)
        success = False
    
    master.respawnInstance()

    print("waiting for old master to show up as follower")
    while not master.ActiveFailoverDetectHostNowFollower():
        print('.')
        time.sleep(1)
    print("Now is follower")
    r = requests.get('http://127.0.0.1:' + master.getFrontendPort())
    print(r)
    print(r.text)
    if r.status_code != 503:
        success = False
    print(success)
    time.sleep(500)

    
class arangoshExecutor(object):
    def __init__(self, username, passvoid, port):
        self.username = username
        self.passvoid = passvoid
        self.port = port;

    def runCommand(self, command):
        cmdstr = ("arangosh" +
                  " --server.endpoint tcp://127.0.0.1:%d" %(self.port) +
                  " --server.username '%s'" % (self.username) +
                  " --server.password '%s'" % (self.passvoid) +
                  " --javascript.execute-string '%s'" % (command))
        print(cmdstr)
        cmd = pexpect.spawnu(cmdstr)
        print("waiting for arangosh to exit")
        print(cmd.after)
        cmd.expect(pexpect.EOF, timeout=30)
        while cmd.isalive():
            print('.')
        return cmd.exitstatus

def LeaderFollower():
    print("launching Leader")
    leader = starterManager('/tmp/lf/leader', mode='single', port=1234)
    print("launching Follower")
    follower = starterManager('/tmp/lf/follower', mode='single', port=2345)
    leaderArangosh = arangoshExecutor(leader.username, leader.passvoid, leader.port + 1)
    followerArangosh = arangoshExecutor(follower.username, follower.passvoid, follower.port + 1)
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

# LeaderFollower();
activeFailover()
