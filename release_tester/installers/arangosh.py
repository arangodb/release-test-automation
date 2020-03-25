import psutil
import installers.log.log as log


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
