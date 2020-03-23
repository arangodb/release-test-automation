import os
import platform
import sys
import re
from abc import ABC, abstractmethod

class installConfig(object):
    def __init__(self, version):
        self.basePath = ""
        self.passvoid = "abc"
        



class installerBase(ABC):
    def installPackage(self):
        pass
    def getAranodConf(self):
        print('sntaohe')
        return '/etc/arangodb3/arangod.conf'


class installerDeb(installerBase):
    def __init__(self):
        print('init')
        print(self.getAranodConf())
    def installPackage(self):
        print(self.getAranodConf())
        import pexpect
        os.environ['DEBIAN_FRONTEND']= 'readline'
        enterprise = 'e';
        version = '3.6.2'
        packageVersion = '1'
        architecture = 'amd64'
        
        serverPackage = 'arangodb3%s_%s-%s_%s.deb' %(enterprise, version, packageVersion, architecture)
        clientPackage = 'arangodb3%s-client_%s-%s_%s.deb'  %(enterprise, version, packageVersion, architecture)
        debugPackage = 'arangodb3%s-dbg_%s-%s_%s.deb'  %(enterprise, version, packageVersion, architecture)
        server = pexpect.spawnu('dpkg -i ' + serverPackage)

        # server.logfile = sys.stdout
        server.expect('user:')
        server.sendline('defg')
        server.expect('user:')
        server.sendline('defg')
        server.expect("Automatically upgrade database files")
        server.sendline("yes")
        server.expect("Database storage engine")
        server.sendline("1")
        server.expect("Backup database files before upgrading")
        server.sendline("no")
        try:
            print("waiting for eof")
            server.expect(pexpect.EOF, timeout=30)
        except server.logfile:
            print("TIMEOUT!")
        #print(server.logfile)
        while server.isalive():
            print('.')
            if server.exitstatus != 0:
                raise Exception("server installation didn't finish successfully!")
        if (not os.path.exists('/var/lib/arangodb3') or
            not os.path.exists('/etc/arangodb3') or
            not os.path.exists('/var/lib/arangodb3')):
            raise Exception("expected installation paths are not there")

        if (not os.path.isfile(self.getAranodConf()) or
            not os.path.isfile('/var/lib/arangodb3/ENGINE')):
            raise Exception("configuration files aren't there")
        print('deb')

class installerRPM(installerBase):
    def installPackage(self):
        import blarg
        print('aoeu')


class installerW(installerBase):
    def installPackage(self):
        print('w')
        import datetime
        import time
        import os
        import sys
        import re
        import shutil
        import psutil

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


basebindirectory = INSTALLATIONFOLDER + '\\'



def get():
    (winver, ,) = platform.win32_ver()
    if winver != "":
        return installerW()
    return installerDeb()
