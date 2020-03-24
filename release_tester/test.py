import sys
import installers.installer as installer


# python3 test.py 3.6.2 enterprise /home/willi/Downloads

if len(sys.argv) != 4:
    print("usage: version enterprise|community packageDir ")
print(sys.argv)

(selffile, version, enterprise, packagedir) = sys.argv
if enterprise == 'enterprise':
    enterprise = True
else:
    enterprise = False

myInstaller = installer.get(version, enterprise, packagedir)

myInstaller.calculatePackageNames()
myInstaller.installPackage()
myInstaller.stopService()
myInstaller.broadcastBind()
myInstaller.startService()
myInstaller.checkInstalledPaths()
myInstaller.checkEngineFile()

input("Press Enter to continue")

myInstaller.unInstallPackage()

myInstaller.checkUninstallCleanup()
