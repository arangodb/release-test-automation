#!/usr/bin/python3
import pexpect
import os

os.environ['DEBIAN_FRONTEND']= 'readline'

child = pexpect.spawnu('dpkg -i arangodb3e_3.6.2-1_amd64.deb')

child.expect('user:')
child.sendline('defg')
child.expect('user:')
child.sendline('defg')
child.expect("Automatically upgrade database files")
child.sendline("yes")
child.expect("Database storage engine")
child.sendline("1")
child.expect("Backup database files before upgrading")
child.sendline("no")

child.expect(pexpect.EOF)
