import re
import time
import installers.log as loglog
log = loglog.log


class arangodLogExaminer(object):
    def __init__(self, config):
        self.cfg = config

    def detectInstancePIDs(self):
        for i in self.cfg.allInstances:
            instance = self.cfg.allInstances[i]
            print(instance)
            instance['PID'] = 0
            while instance['PID'] == 0:
                lfh = open(instance['logfile'])
                lastLine = ''
                lf = ''
                for line in lfh:
                    if line == "":
                        continue
                    lastLine = line
                    lf += '\n' + line
                print(lastLine)
                m = re.search(r'Z \[(\d*)\]', lastLine)
                if m == None:
                    log("no PID in: " + lastLine)
                    continue
                pid = m.groups()[0]
                start = lf.find(pid)
                pos = lf.find('is ready for business.', start)
                if pos < 0:
                    log('.')
                    time.sleep(1)
                    continue
                instance['PID'] = int(pid)
        log(str(self.cfg.allInstances))
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
