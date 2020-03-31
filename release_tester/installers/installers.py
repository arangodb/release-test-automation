#!/usr/bin/env python3

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
import installers.arangodlog as arangodLog
from logging import info as log
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
from pathlib import Path
from abc import abstractmethod, ABC
__name__ = "installers"

class installConfig(object):
    def __init__(self, version, enterprise, packageDir, publicip, yamlcfg=None):
        if yamlcfg != None:
            self.publicip = publicip
            self.basePath = Path("/")
            self.username = "root"
            self.passvoid = "abc"
            self.enterprise = enterprise
            self.version = version
            self.packageDir = packageDir
            self.installPrefix = ''
            self.jwt = ''
            self.port=8529
            self.allInstances = {}
        else:
            self.publicip = publicip
            self.basePath = Path("/")
            self.username = "root"
            self.passvoid = "abc"
            self.enterprise = enterprise
            self.version = version
            self.packageDir = packageDir
            self.installPrefix = Path('/')
            self.jwt = ''
            self.port=8529
            self.allInstances = {}

    def generatePassword(self):
        self.passvoid = 'cde'

class installerBase(ABC):
    @abstractmethod
    def calculatePackageNames(self):
        pass
    @abstractmethod
    def installPackage(self):
        pass
    @abstractmethod
    def unInstallPackage(self):
        pass
    @abstractmethod
    def checkServiceUp(self):
        pass
    @abstractmethod
    def startService(self):
        pass
    @abstractmethod
    def stopService(self):
        pass

    def getArangodConf(self):
        return self.cfg.cfgdir / 'arangod.conf'

    def calcConfigFileName(self):
        cfgFile = Path()
        if self.cfg.installPrefix == Path('/'):
            cfgFile = Path('/') / 'tmp' / 'config.yml'
        else:
            cfgFile = Path('c:') / 'tmp' / 'config.yml'
        return cfgFile;

    def saveConfig(self):
        import yaml
        self.calcConfigFileName().write_text(yaml.dump(self.cfg))

    def loadConfig(self):
        import yaml
        with open(self.calcConfigFileName()) as fh:
            self.cfg = yaml.load(fh, Loader=yaml.Loader)
        self.logExaminer = arangodLog.arangodLogExaminer(self.cfg);

    def broadcastBind(self):
        arangodconf = None
        with open(self.getArangodConf(), 'r') as fh:
            arangodconf = fh.read()
        ipMatch = re.compile('127\\.0\\.0\\.1')
        newArangodConf = ipMatch.subn('0.0.0.0', arangodconf)
        with open(self.getArangodConf(), 'w') as fh:
            fh.write(newArangodConf[0])
        log("arangod now configured for broadcast bind")

    def enableLogging(self):
        arangodconf = None
        with open(self.getArangodConf(), 'r') as fh:
            arangodconf = fh.read()
        print(arangodconf)
        self.cfg.logDir.mkdir(parents=True)
        newArangodConf = arangodconf.replace('[log]', '[log]\nfile = ' + str(self.cfg.logDir / 'arangod.log'))
        print(newArangodConf)
        with open(self.getArangodConf(), 'w') as fh:
            fh.write(newArangodConf)
        log("arangod now configured for logging")

    def checkInstalledPaths(self):
        if (not self.cfg.dbdir.is_dir() or
            not self.cfg.appdir.is_dir() or
            not self.cfg.cfgdir.is_dir()):
            raise Exception("expected installation paths are not there")

        if not self.getArangodConf().is_file():
            raise Exception("configuration files aren't there")
    def checkEngineFile(self):
        if not Path(self.cfg.dbdir / 'ENGINE').is_file():
            raise Exception("database engine file not there!")

    def checkUninstallCleanup(self):
        success = True

        if (self.cfg.installPrefix != Path("/") and
            self.cfg.installPrefix.is_dir()):
            log("Path not removed: " + str(self.cfg.installPrefix))
            success = False
        if os.path.exists(self.cfg.appdir):
            log("Path not removed: " + str(self.cfg.appdir))
            success = False
        if os.path.exists(self.cfg.dbdir):
            log("Path not removed: " + str(self.cfg.dbdir))
            success = False
        return success


class installerDeb(installerBase):
    def __init__(self, installConfig):
        self.cfg = installConfig
        self.cfg.baseTestDir = Path('/tmp')

    def calculatePackageNames(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        packageVersion = '1'
        architecture = 'amd64'

        desc = { "ep": enterprise
               , "cfg" : self.cfg.version
               , "ver" : packageVersion
               , "arch" : architecture
               }

        self.serverPackage = 'arangodb3{ep}_{cfg}-{ver}_{arch}.deb'.format(**desc)
        self.clientPackage = 'arangodb3{ep}-client_{cfg}-{ver}_{arch}.deb'.format(**desc)
        self.debugPackage = 'arangodb3{ep}-dbg_{cfg}-{ver}_{arch}.deb'.format(**desc)

    def checkServiceUp(self):
        time.sleep(1) # TODO

    def startService(self):
        import pexpect
        startServer = pexpect.spawnu('service arangodb3 start')
        log("waiting for eof")
        startServer.expect(pexpect.EOF, timeout=30)
        while startServer.isalive():
            log('.')
            if startServer.exitstatus != 0:
                raise Exception("server service start didn't finish successfully!")
        time.sleep(0.1)
        self.logExaminer.detectInstancePIDs()

    def stopService(self):
        import pexpect
        stopServer = pexpect.spawnu('service arangodb3 stop')
        log("waiting for eof")
        stopServer.expect(pexpect.EOF, timeout=30)
        while stopServer.isalive():
            log('.')
            if stopServer.exitstatus != 0:
                raise Exception("server service stop didn't finish successfully!")

    def installPackage(self):
        import pexpect
        self.cfg.installPrefix = Path("/")
        self.cfg.logDir = Path('/var/log/arangodb3')
        self.cfg.dbdir = Path('/var/lib/arangodb3')
        self.cfg.appdir = Path('/var/lib/arangodb3-apps')
        self.cfg.cfgdir = Path('/etc/arangodb3')
        log("installing Arangodb debian package")
        os.environ['DEBIAN_FRONTEND']= 'readline'
        serverInstall = pexpect.spawnu('dpkg -i ' +
                                       str(self.cfg.packageDir / self.serverPackage))
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
            log("waiting for the installation to finish")
            serverInstall.expect(pexpect.EOF, timeout=30)
        except serverInstall.logfile:
            log("TIMEOUT!")
        while serverInstall.isalive():
            log('.')
            if serverInstall.exitstatus != 0:
                raise Exception("server installation didn't finish successfully!")
        log('Installation successfull')
        self.cfg.allInstances = {
            'single': {
                'logfile': self.cfg.installPrefix / '/var/log/arangodb3/arangod.log'
            }
        }
        self.logExaminer = arangodLog.arangodLogExaminer(self.cfg);
        self.logExaminer.detectInstancePIDs()

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
        self.cfg.installPrefix = Path("C:/tmp")
        self.cfg.baseTestDir = Path('/tmp')

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
        from pathlib import PureWindowsPath
        self.cfg.logDir = self.cfg.installPrefix / "LOG"
        self.cfg.dbdir = self.cfg.installPrefix / "DB"
        self.cfg.appdir = self.cfg.installPrefix / "APP"
        self.cfg.installPrefix = self.cfg.installPrefix / "PROG"
        self.cfg.cfgdir = self.cfg.installPrefix / 'etc/arangodb3'
        cmd = [str(self.cfg.packageDir / self.serverPackage),
               '/PASSWORD=' + self.cfg.passvoid,
               '/INSTDIR=' + str(PureWindowsPath(self.cfg.installPrefix)),
               '/DATABASEDIR=' + str(PureWindowsPath(self.cfg.dbdir)),
               '/APPDIR=' + str(PureWindowsPath(self.cfg.appdir)),
               '/PATH=0',
               '/S',
               '/INSTALL_SCOPE_ALL=1']
        log('running windows package installer:')
        log(str(cmd))
        install = psutil.Popen(cmd)
        install.wait()
        self.service = psutil.win_service_get('ArangoDB')
        while not self.checkServiceUp():
            log('starting...')
            time.sleep(1)
        self.enableLogging()
        self.stopService()
        time.sleep(1)
        self.cfg.allInstances = {
            'single': {
                'logfile': self.cfg.logDir / 'arangod.log'
            }
        }
        self.logExaminer = arangodLog.arangodLogExaminer(self.cfg);
        self.startService()
        log('Installation successfull')

    def unInstallPackage(self):
        from pathlib import PureWindowsPath
        self.getArangodConf().unlink() # once we modify it, the uninstaller will leave it there...
        uninstaller="Uninstall.exe"
        tmp_uninstaller=Path("c:/tmp") / uninstaller
        # copy out the uninstaller as the windows facility would do:
        shutil.copyfile(self.cfg.installPrefix / uninstaller, tmp_uninstaller)

        cmd = [tmp_uninstaller, '/PURGE_DB=1', '/S', '_?=' + str(PureWindowsPath(self.cfg.installPrefix))]
        log('running windows package uninstaller')
        log(str(cmd))
        uninstall = psutil.Popen(cmd)
        uninstall.wait()
        shutil.rmtree(self.cfg.logDir)
        tmp_uninstaller.unlink()
        time.sleep(2)
        try:
            log(psutil.win_service_get('ArangoDB'))
            service = psutil.win_service_get('ArangoDB')
            if service.status() != 'stopped':
                log("service shouldn't exist anymore!")
                success = False
        except:
            pass

    def checkServiceUp(self):
        return self.service.status() == 'running'

    def startService(self):
        self.service.start()
        while self.service.status() != "running":
            log(self.service.status())
            time.sleep(1)
            if self.service.status() == "stopped":
                raise Exception("arangod service stopped again on its own! Configuration / Port problem?")
        self.logExaminer.detectInstancePIDs()

    def stopService(self):
        self.service.stop()
        while self.service.status() != "stopped":
            log(self.service.status())
            time.sleep(1)


def get(*args, **kwargs):
    (winver, x, y, z) = platform.win32_ver()
    if winver:
        return installerW(installConfig(*args, **kwargs))
    return installerDeb(installConfig(*args, **kwargs))
