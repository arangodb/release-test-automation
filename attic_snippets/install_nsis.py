import datetime
import time
import os
import sys
import re
import shutil
import psutil
import win32serviceutil

COMPACT_VERSION='3.6.2'
# COMPACT_VERSION='3.3.25-1'
installPrefix= "c:/Programme/ArangoDB3e 3.6.2/" 
installPrefix="C:/tmp"

INSTALLER = "c:/Users/willi/Downloads/ArangoDB3e-" + COMPACT_VERSION + "_win64.exe"

success = True
UNINSTALLER="Uninstall.exe"
TMP_UNINSTALLER="c:/tmp/" + UNINSTALLER
PASSWORD='passvoid'

INSTALLATIONFOLDER = os.path.join(re.sub('/', '\\\\', installPrefix), "PROG")
DBFOLDER = re.sub('/', '\\\\', installPrefix + "/DB")
APPFOLDER = re.sub('/', '\\\\', installPrefix + "/APP")
PASSWORD = "ABCDE"


basebindirectory = INSTALLATIONFOLDER + '\\'
def timestamp():
    return datetime.datetime.utcnow().isoformat()
def log(string):
    print(timestamp() + " " + string)

class arangoshExecutor(object):
    def __init__(self, username, port=8529, passvoid="", jwt=None):
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




cmd = [INSTALLER,
      '/PASSWORD=' + PASSWORD,
      '/INSTDIR=' + INSTALLATIONFOLDER,
      '/DATABASEDIR=' + DBFOLDER,
      '/APPDIR=' + APPFOLDER,
      '/PATH=0',
      '/S',
      '/INSTALL_SCOPE_ALL=1']

print(cmd)
install = psutil.Popen(cmd)
install.wait()
print ("x"*80)

jsVersionCheck = '''
if (db._version()!='%s') { throw 'fail'}
''' % (COMPACT_VERSION)
arangosh = arangoshExecutor(username='root', passvoid=PASSWORD)
print(jsVersionCheck)

service = psutil.win_service_get('ArangoDB')

print(service.status())
if service.status() == 'running':
    print("arangod running - first check with arangosh: ")
    rc = arangosh.runCommand(jsVersionCheck, 'check version')
    if rc != 0:
        print("arangosh exited with failure!")
        success = False
    service.stop()
while service.status() != "stopped":
    print(service.status())
    time.sleep(1)
service.start()

while service.status() != "running":
    print(service.status())
    time.sleep(1)
rc = arangosh.runCommand(jsVersionCheck, 'check version')
if rc != 0:
    print("arangosh exited with failure!")
    success = False





# copy out the uninstaller as the windows facility would do:
shutil.copyfile(os.path.join(INSTALLATIONFOLDER, UNINSTALLER), TMP_UNINSTALLER)

cmd = [TMP_UNINSTALLER, '/PURGE_DB=1', '/S', '_?=' + INSTALLATIONFOLDER]
print(cmd)

uninstall = psutil.Popen(cmd)
uninstall.wait()

if os.path.exists(INSTALLATIONFOLDER):
    print("Path not removed: " + INSTALLATIONFOLDER)
    success = False
if os.path.exists(APPFOLDER):
    print("Path not removed: " + APPFOLDER)
    success = False
if os.path.exists(DBFOLDER):
    print("Path not removed: " + DBFOLDER)
    success = False

try:
    print(psutil.win_service_get('ArangoDB'))
    service = psutil.win_service_get('ArangoDB')
    if service.status() != 'stopped':
        print("service shouldn't exist anymore!")
        success = False
except:
    pass

if not success:
    print("exiting with failure.")
    sys.exit(1)
sys.exit(0)
