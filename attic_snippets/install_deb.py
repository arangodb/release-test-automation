#!/usr/bin/python3
import pexpect
import os
import sys
import re

os.environ['DEBIAN_FRONTEND']= 'readline'


arangoConfFN = '/etc/arangodb3/arangod.conf'

enterprise = 'e';

version = '3.6.2'
packageVersion = '1'
architecture = 'amd64'

serverPackage = 'arangodb3%s_%s-%s_%s.deb' %(enterprise, version, packageVersion, architecture)
clientPackage = 'arangodb3%s-client_%s-%s_%s.deb'  %(enterprise, version, packageVersion, architecture)
debugPackage = 'arangodb3%s-dbg_%s-%s_%s.deb'  %(enterprise, version, packageVersion, architecture)

# sys.stdout.reconfigure(encoding='ascii')

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

if (not os.path.isfile(arangoConfFN) or
    not os.path.isfile('/var/lib/arangodb3/ENGINE')):
    raise Exception("configuration files aren't there")

arangodconf = open(arangoConfFN, 'r').read()

ipMatch = re.compile('127\\.0\\.0\\.1')

newArangodConf = ipMatch.subn('0.0.0.0', arangodconf)
print(newArangodConf)
open(arangoConfFN, 'w').write(newArangodConf[0])

stopServer = pexpect.spawnu('service arangodb3 stop')
print("waiting for eof")
stopServer.expect(pexpect.EOF, timeout=30)
while stopServer.isalive():
    print('.')
if stopServer.exitstatus != 0:
    raise Exception("server service stop didn't finish successfully!")


startServer = pexpect.spawnu('service arangodb3 start')
print("waiting for eof")
startServer.expect(pexpect.EOF, timeout=30)
while startServer.isalive():
    print('.')
if startServer.exitstatus != 0:
    raise Exception("server service start didn't finish successfully!")




debug = pexpect.spawnu('dpkg -i ' + debugPackage)

debug.expect('Setting up')
debug.expect(pexpect.EOF)

client = pexpect.spawnu('dpkg -i ' + clientPackage)
print('waiting for apt to conflict')
client.expect('conflict')

client.expect(pexpect.EOF)

