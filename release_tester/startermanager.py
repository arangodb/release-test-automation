import os
import psutil
from logging import info as log
from installers.arangosh import arangoshExecutor
from pathlib import Path

class starterManager(object):
    def __init__(self, basedir, installprefix, mode=None, port=None, jwtStr=None, moreopts=[]):
        self.basedir = basedir
        self.installprefix
        self.logfileName = basedir / "arangodb.log"
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
        self.moreopts = [];
        if self.mode:
            self.moreopts += ["--starter.mode", self.mode]
        self.moreopts += moreopts
        self.jwtfile = Path()
        if jwtStr:
            print("JWT!")
            os.makedirs(self.basedir)
            self.jwtfile = self.basedir / 'jwt'
            f = open(jwtfile, 'w')
            f.write(jwtStr)
            f.close()
            self.moreopts = ['--auth.jwt-secret', str(self.jwtfile)] + self.moreopts
        if self.port != None:
            self.frontendPort = port + 1
            self.moreopts += ["--starter.port", "%d" % port]
        self.arguments = [self.installprefix / 'usr' / 'bin' / 'arangodb',
                          "--log.console=false",
                          "--log.file=true",
                          "--starter.data-dir=%s" % self.basedir
        ] + self.moreopts

    def runStarter(self):
        log("launching " + str(self.arguments))
        self.instance = psutil.Popen(self.arguments)
        time.sleep(self.startupwait)

    def executeFrontend(self, cmd):
        if self.arangoshExecutor == None:
            self.arangoshExecutor = arangoshExecutor(username="root", port=int(self.frontendPort), passvoid="")
        return self.arangoshExecutor.runCommand(cmd)

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
