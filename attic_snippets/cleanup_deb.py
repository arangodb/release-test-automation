#!/usr/bin/python3
import pexpect
import os

os.environ['DEBIAN_FRONTEND']= 'readline'

enterprise = 'e';

version = '3.6.2'
packageVersion = '1'
architecture = 'amd64'

serverPackage = 'arangodb3%s_%s-%s_%s.deb' %(enterprise, version, packageVersion, architecture)
clientPackage = 'arangodb3%s-client_%s-%s_%s.deb'  %(enterprise, version, packageVersion, architecture)
debugPackage = 'arangodb3%s-dbg_%s-%s_%s.deb'  %(enterprise, version, packageVersion, architecture)

serverPackageName = 'arangodb3%s' %(enterprise)
clientPackageName = 'arangodb3%s-client'  %(enterprise)
debugPackageName = 'arangodb3%s-dbg'  %(enterprise)


print("uninstalling arangod")
server = pexpect.spawnu('dpkg --purge ' + serverPackageName)
print("waiting for finish")
server.expect(pexpect.EOF)
print("done")

print("uninstall debug package")
debug = pexpect.spawnu('dpkg --purge ' + debugPackageName)
print("waiting")
debug.expect(pexpect.EOF)
print("done")


print("uninstalling arangod")
server = pexpect.spawnu('dpkg --purge ' + serverPackageName)
print("waiting for finish")
server.expect(pexpect.EOF)
print("done")
