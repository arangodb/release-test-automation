import sys
import time
import os
import shutil
import logging
from pathlib import Path
import pexpect
from arangodb.instance import ArangodInstance
from arangodb.installers.base import InstallerBase
from tools.asciiprint import ascii_print
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
import tools.loghelper as lh
import semver

class InstallerLinux(InstallerBase):
    def __init__(self, cfg):

        super().__init__(cfg)
    

    def gdb_test(self):
        """ gdb check for arangod in /sbin folder before installing the package """
        gdb = pexpect.spawnu('gdb /usr/sbin/arangod')
        i = gdb.expect(['Reading symbols from /usr/lib/debug/', '(No debugging symbols found in /usr/sbin/arangod)', '(gdb)'])
        if i in [0, 2]:
            logging.info("debugging symbol found")
            gdb.sendline('quit')
            logging.info('Quiting gdb session.')
            gdb.terminate(force=True)
        elif i in [1, 2]:
            logging.info("No debugging symbol found")
            gdb.sendline('quit')
            logging.info('Quiting gdb session.')
            gdb.terminate(force=True)
        else:
            logging.info('Something wrong')
            sys.exit(1)
            