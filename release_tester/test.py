#/usr/bin/env python3
import sys
import click
import installers.installers as installers
from installers.arangosh import arangoshExecutor
from logging import info as log
import logging
import psutil
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
    def killallprocesses():
        arangods = []
        arangodbs = []
        arangosyncs = []
        log("searching for leftover processes")
        for process in psutil.process_iter(['pid', 'name']):
            if process.name() == 'arangod':
                arangods.append(process)
            if process.name() == 'arangodb':
                arangodbs.append(process)
            if process.name() == 'arangosync':
                arangosyncs.append(process)
            
        for process in arangosyncs:
            log("cleanup killing " + str(process))
            p = psutil.process(process.pid)
            p.terminate()
            p.wait()
        for process in arangodbs:
            log("cleanup killing " + str(process))
            p = psutil.process(process.pid)
            p.terminate()
            p.wait()
        for process in arangods:
            log("cleanup killing " + str(process))
            p = psutil.process(process.pid)
            p.terminate()
            p.wait()
    enterprise = enterprise == 'True'
    jsVersionCheck = (
        "if (db._version()!='%s') { throw 'fail'}" % (version),
        'check version')
    if mode not in ['all', 'install', 'tests', 'uninstall']:
        raise Exception("unsupported mode!")
    myInstaller = installers.get(version, enterprise, Path(package_dir), publicip)
    
    myInstaller.calculatePackageNames()
    if mode == 'all' or mode == 'install':
        killallprocesses()
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
        myInstaller.startService()
        
        systemInstallArangosh = arangoshExecutor(myInstaller.cfg)
        
        if not systemInstallArangosh.runCommand(jsVersionCheck):
            log("Version Check failed!")
        input("Press Enter to continue")
        myInstaller.stopService()
        killallprocesses()
        for runner  in [runnertype.LEADER_FOLLOWER,
                        runnertype.ACTIVE_FAILOVER,
                        runnertype.CLUSTER,
                        runnertype.DC2DC]:
            stenv = getStarterenv(runner, myInstaller.cfg)
            stenv.setup()
            stenv.run()
            stenv.postSetup()
            stenv.jamAttempt()
            input("Press Enter to continue")
            stenv.shutdown()
            stenv.cleanup()
            killallprocesses()
    
    if mode == 'all' or mode == 'uninstall':
        myInstaller.unInstallPackage()
        myInstaller.checkUninstallCleanup()

if __name__ == "__main__": 
    runTest()
