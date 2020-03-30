import sys
import installers.installer as installer
from installers.arangosh import arangoshExecutor
from logging import info as log
import logging
from pathlib import Path
from installers.starterenvironment import get as getStarterenv
from installers.starterenvironment import runnertype
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

# python test.py 3.6.2 enterprise c:/Users/willi/Downloads all

# python3 test.py 3.6.2 enterprise /home/willi/Downloads all

if len(sys.argv) != 5:
    print("usage: version [enterprise|community] packageDir [all|install|uninstall|tests]")
print(sys.argv)

(selffile, version, enterprise, packagedir, runmode) = sys.argv
if enterprise == 'enterprise':
    enterprise = True
else:
    enterprise = False

jsVersionCheck = (
    "if (db._version()!='%s') { throw 'fail'}" % (version),
    'check version')

myInstaller = installer.get(version, enterprise, Path(packagedir))

myInstaller.calculatePackageNames()
if runmode == 'all' or runmode == 'install':
    myInstaller.installPackage()
    myInstaller.saveConfig()
else:
    myInstaller.loadConfig()

if runmode == 'all' or runmode == 'tests':
    #myInstaller.stopService()
    #myInstaller.broadcastBind()
    #myInstaller.startService()
    #myInstaller.checkInstalledPaths()
    #myInstaller.checkEngineFile()
    #
    #systemInstallArangosh = arangoshExecutor(myInstaller.cfg)
    #
    #if not systemInstallArangosh.runCommand(jsVersionCheck):
    #    log("Version Check failed!")
    #input("Press Enter to continue")

    stenv = getStarterenv(runnertype.LEADER_FOLLOWER, myInstaller.cfg)

    stenv.setup()
    stenv.run()
    stenv.postSetup()
    stenv.jamAttempt()
    input("Press Enter to continue")
    stenv.shutdown()

if runmode == 'all' or runmode == 'uninstall':
    myInstaller.unInstallPackage()
    myInstaller.checkUninstallCleanup()
