#!/usr/bin/python3
import pexpect
import os
import sys
import logging


#gdb check for arangod in /sbin folder before installing the package
gdb = pexpect.spawnu('gdb /usr/sbin/arangod')
i = gdb.expect(['Reading symbols from /usr/lib/debug/', '(No debugging symbols found in /usr/sbin/arangod)', '(gdb)'])
if i in [0, 2]:
    logging.info("debugging symbol found")
    gdb.sendline('quit')
    logging.info('Quiting gdb session.')
elif i in [1, 2]:
    logging.info("No debugging symbol found")
    gdb.sendline('quit')
    logging.info('Quiting gdb session.')
else:
    logging.info('Something wrong')