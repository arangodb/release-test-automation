#/usr/bin/env python3
import sys
import click
import installers.installers as installers
from installers.arangosh import arangoshExecutor
from logging import info as log
import logging
from pathlib import Path
from installers.starterenvironment import get as getStarterenv
from installers.starterenvironment import runnertype
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

@click.command()
@click.option('--version', help='ArangoDB version number.')
@click.option('--package-dir', default='/tmp/', help='directory to load the packages from.')
@click.option('--enterprise', default='True', help='Enterprise or community?')
@click.option('--mode', default='all', help='operation mode - [all|install|uninstall|tests].')
@click.option('--publicip', default='127.0.0.1', help='IP for the click to browser hints.')

def runTest(version, package_dir, enterprise, mode, publicip):
    enterprise = enterprise == 'True'
    jsVersionCheck = (
        "if (db._version()!='%s') { throw 'fail'}" % (version),
        'check version')
    
    myInstaller = installers.get(version, enterprise, Path(package_dir), publicip)
    
    myInstaller.calculatePackageNames()
    if mode == 'all' or mode == 'install':
        myInstaller.installPackage()
        myInstaller.saveConfig()
        myInstaller.stopService()
        myInstaller.broadcastBind()
        myInstaller.startService()
        myInstaller.checkInstalledPaths()
        myInstaller.checkEngineFile()
    else:
        myInstaller.loadConfig()
    
    if mode == 'all' or mode == 'tests':
        myInstaller.stopService()
        #myInstaller.startService()
        #
        #systemInstallArangosh = arangoshExecutor(myInstaller.cfg)
        #
        #if not systemInstallArangosh.runCommand(jsVersionCheck):
        #    log("Version Check failed!")
        #input("Press Enter to continue")
        myInstaller.stopService()
    
        # stenv = getStarterenv(runnertype.LEADER_FOLLOWER, myInstaller.cfg)
        #stenv = getStarterenv(runnertype.ACTIVE_FAILOVER, myInstaller.cfg)
        # stenv = getStarterenv(runnertype.CLUSTER, myInstaller.cfg)
        stenv = getStarterenv(runnertype.DC2DC, myInstaller.cfg)
        stenv.setup()
        stenv.run()
        stenv.postSetup()
        stenv.jamAttempt()
        input("Press Enter to continue")
        stenv.shutdown()
    
    if mode == 'all' or mode == 'uninstall':
        myInstaller.unInstallPackage()
        myInstaller.checkUninstallCleanup()

if __name__ == "__main__": 
    runTest()
