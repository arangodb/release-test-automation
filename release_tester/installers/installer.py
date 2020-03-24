import datetime
import time
import os
import sys
import re
import shutil
import psutil
import os
import platform
import sys
import re
from abc import ABC, abstractmethod

class installConfig(object):
    def __init__(self, version, enterprise, packageDir):
        self.basePath = ""
        self.passvoid = "abc"
        self.enterprise = enterprise
        self.version = version
        self.packageDir = packageDir
        self.installPrefix = ''

    def generatePassword(self):
        self.passvoid = 'cde'


class installerBase(ABC):
    def calculatePackageNames(self):
        pass
    def installPackage(self):
        pass
    def unInstallPackage(self):
        pass
    def checkServiceUp(self):
        pass
    def startService(self):
        pass
    def stopService(self):
        pass
    def getAranodConf(self):
        print('sntaohe')
        return os.path.join(self.cfg.cfgdir, 'arangod.conf')

    def broadcastBind(self):
        arangodconf = open(self.getAranodConf(), 'r').read()
        ipMatch = re.compile('127\\.0\\.0\\.1')
        newArangodConf = ipMatch.subn('0.0.0.0', arangodconf)
        open(self.getAranodConf(), 'w').write(newArangodConf[0])
        print("arangod now configured for broadcast bind")

    def checkInstalledPaths(self):
        if (not os.path.exists(self.cfg.dbdir) or
            not os.path.exists(self.cfg.appdir) or
            not os.path.exists(self.cfg.cfgdir)):
            raise Exception("expected installation paths are not there")

        if not os.path.isfile(self.getAranodConf()):
            raise Exception("configuration files aren't there")
    def checkEngineFile(self):
        if not os.path.isfile(os.path.join(self.cfg.dbdir, 'ENGINE')):
            raise Exception("database engine file not there!")

    def checkUninstallCleanup(self):
        success = True
        if (self.cfg.installPrefix != "" and
            os.path.exists(self.cfg.installPrefix)):
            print("Path not removed: " + self.cfg.installPrefix)
            success = False
        if os.path.exists(self.cfg.appdir):
            print("Path not removed: " + self.cfg.appdir)
            success = False
        if os.path.exists(self.cfg.dbdir):
            print("Path not removed: " + self.cfg.dbdir)
            success = False
        return success


class installerDeb(installerBase):
    def __init__(self, installConfig):
        self.cfg = installConfig
        print('init')
        # print(self.getAranodConf())

    def calculatePackageNames(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        packageVersion = '1'
        architecture = 'amd64'

        self.serverPackage = 'arangodb3%s_%s-%s_%s.deb' %(
            enterprise,
            self.cfg.version,
            packageVersion,
            architecture)
        self.clientPackage = 'arangodb3%s-client_%s-%s_%s.deb'  %(
            enterprise,
            self.cfg.version,
            packageVersion,
            architecture)
        self.debugPackage = 'arangodb3%s-dbg_%s-%s_%s.deb'  %(
            enterprise,
            self.cfg.version,
            packageVersion,
            architecture)

    def checkServiceUp(self):
        time.sleep(1) # TODO

    def startService(self):
        import pexpect
        startServer = pexpect.spawnu('service arangodb3 start')
        print("waiting for eof")
        startServer.expect(pexpect.EOF, timeout=30)
        while startServer.isalive():
            print('.')
            if startServer.exitstatus != 0:
                raise Exception("server service start didn't finish successfully!")

    def stopService(self):
        import pexpect
        stopServer = pexpect.spawnu('service arangodb3 stop')
        print("waiting for eof")
        stopServer.expect(pexpect.EOF, timeout=30)
        while stopServer.isalive():
            print('.')
            if stopServer.exitstatus != 0:
                raise Exception("server service stop didn't finish successfully!")

    def installPackage(self):
        import pexpect
        self.cfg.installPrefix = os.path.join(re.sub('/', '\\\\', self.cfg.installPrefix), "PROG")
        self.cfg.dbdir = '/var/lib/arangodb3'
        self.cfg.appdir = '/var/lib/arangodb3-apps'
        self.cfg.cfgdir = '/etc/arangodb3'
        print("installing Arangodb debian package")
        os.environ['DEBIAN_FRONTEND']= 'readline'
        serverInstall = pexpect.spawnu('dpkg -i ' +
                                       os.path.join(self.cfg.packageDir,
                                                    self.serverPackage))
        serverInstall.expect('user:')
        serverInstall.sendline(self.cfg.passvoid)
        serverInstall.expect('user:')
        serverInstall.sendline(self.cfg.passvoid)
        serverInstall.expect("Automatically upgrade database files")
        serverInstall.sendline("yes")
        serverInstall.expect("Database storage engine")
        serverInstall.sendline("1")
        serverInstall.expect("Backup database files before upgrading")
        serverInstall.sendline("no")
        try:
            print("waiting for the installation to finish")
            serverInstall.expect(pexpect.EOF, timeout=30)
        except serverInstall.logfile:
            print("TIMEOUT!")
        #print(server.logfile)
        while serverInstall.isalive():
            print('.')
            if serverInstall.exitstatus != 0:
                raise Exception("server installation didn't finish successfully!")
        print('Installation successfull')

    def unInstallPackage(self):
        import pexpect
        uninstall = pexpect.spawnu('dpkg --purge ' + 'arangodb3' + 'e' if self.cfg.enterprise else '')

        uninstall.expect('Purging')
        uninstall.expect(pexpect.EOF)
        


class installerRPM(installerBase):
    def __init__(self, installConfig):
        self.cfg = installConfig
    def installPackage(self):
        import blarg
        print('aoeu')


class installerW(installerBase):

    def __init__(self, installConfig):
        self.cfg = installConfig
        self.cfg.installPrefix="C:/tmp"

    def calculatePackageNames(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        architecture = 'win64'
        self.serverPackage = 'ArangoDB3%s-%s_%s.exe' %(
            enterprise,
            self.cfg.version,
            architecture)
        self.clientPackage = 'ArangoDB3%s-client_%s_%s.exe'  %(
            enterprise,
            self.cfg.version,
            architecture)

    def installPackage(self):
        print('w')
        self.cfg.dbdir = re.sub('/', '\\\\', self.cfg.installPrefix + "/DB")
        self.cfg.appdir = re.sub('/', '\\\\', self.cfg.installPrefix + "/APP")
        self.cfg.installPrefix = os.path.join(re.sub('/', '\\\\', self.cfg.installPrefix), "PROG")
        self.cfg.cfgdir = re.sub('/', '\\\\', self.cfg.installPrefix + '/etc/arangodb3')
        cmd = [os.path.join(self.cfg.packageDir, self.serverPackage),
               '/PASSWORD=' + self.cfg.passvoid,
               '/INSTDIR=' + self.cfg.installPrefix,
               '/DATABASEDIR=' + dbdir,
               '/APPDIR=' + appdir,
               '/PATH=0',
               '/S',
               '/INSTALL_SCOPE_ALL=1']
        print('running windows package installer:')
        print(cmd)
        install = psutil.Popen(cmd)
        install.wait()
        self.service = psutil.win_service_get('ArangoDB')
        print('Installation successfull')

    def unInstallPackage(self):
        uninstaller="Uninstall.exe"
        tmp_uninstaller=path.join("c:/tmp/", uninstaller)
        # copy out the uninstaller as the windows facility would do:
        shutil.copyfile(os.path.join(self.cfg.installPrefix, uninstaller), tmp_uninstaller)

        cmd = [tmp_uninstaller, '/PURGE_DB=1', '/S', '_?=' + self.cfg.installPrefix]
        print('running windows package uninstaller')
        print(cmd)
        uninstall = psutil.Popen(cmd)
        uninstall.wait()

        try:
            print(psutil.win_service_get('ArangoDB'))
            service = psutil.win_service_get('ArangoDB')
            if service.status() != 'stopped':
                print("service shouldn't exist anymore!")
                success = False
        except:
            pass

    def checkServiceUp(self):
        return self.service.status() == 'running'

    def startService(self):
        self.service.start()
        while self.service.status() != "running":
            print(self.service.status())
            time.sleep(1)

    def stopService(self):
        self.service.stop()
        while self.service.status() != "stopped":
            print(self.service.status())
            time.sleep(1)


def get(*args, **kwargs):
    (winver, x, y, z) = platform.win32_ver()
    if winver != "":
        return installerW(installConfig(*args, **kwargs))
    return installerDeb(installConfig(*args, **kwargs))
