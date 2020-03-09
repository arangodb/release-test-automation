import time
import pexpect
import os
import sys
import re

class starterManager(object):
    def __init__(self, basedir, mode, port, moreopts = ""):
        self.basedir = basedir
        self.logfileName = basedir + "/arangodb.log" 
        self.port = port
        self.username = 'root'
        self.passvoid = ''
        self.mode = mode
        if self.port != None:
            moreopts += " --starter.port %d" % port
        self.instance = pexpect.spawnu("arangodb --log.console=false --log.file=true --starter.data-dir=%s --starter.mode %s %s" % (
            self.basedir,
            self.mode,
            moreopts))
        time.sleep(1)
    
    def getLogFile(self):
        return open(self.logfileName).read()
    
    def isInstanceUp(self):
        if not self.instance.isalive():
            raise Exception("my instance is gone! " + self.basedir)
        lf = self.getLogFile()
        return lf.find('Your single server can now be accessed') >= 0

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
""" % (leader.port)

beforeReplJS = """
db._create("testCollectionBefore");
db.testCollection.save({"hello": "world"})
"""
afterReplJS =  """
db._create("testCollectionAfter");
db.testCollection.save({"hello": "world"})
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
