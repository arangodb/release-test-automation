#!/usr/bin/python3
import pexpect
import os
import sys
import re

installStrippedBinaries = [
    '/usr/bin/arangobackup',# enterprise
    '/usr/bin/arangoexport',
    '/usr/bin/arangoimport',
    '/usr/bin/arangorestore',
    '/usr/bin/arangobench',
    '/usr/bin/arangodump',
    '/usr/bin/arangosh',
    '/usr/bin/arangovpack',
    '/usr/sbin/arangod',
    '/usr/sbin/rclone-arangodb'] # enterprise
installNonStrippedBinaries = [
    '/usr/sbin/arangosync', # enterprise
    '/usr/bin/arangodb']
installSymlinks = [
    '/usr/bin/arangoimp',
    '/usr/bin/arangoinspect',
    '/usr/bin/arangosync', # enterprise
    '/usr/sbin/arango-dfdb',
    '/usr/sbin/arango-init-database',
    '/usr/sbin/arango-secure-installation']



for symlink in installSymlinks:
    if not os.path.islink(symlink):
        raise Exception(" expected " + symlink + " to be a symlink ")

for strippedFile in installStrippedBinaries:
    fileData = pexpect.spawnu('file ' + strippedFile)
    output = fileData.readline();
    if output.find(', stripped') < 0:
        raise Exception("expected " + strippedFile + " to be stripped, but its not: " + output)

for nonStrippedFile in installNonStrippedBinaries:
    fileData = pexpect.spawnu('file ' + nonStrippedFile)
    output = fileData.readline();
    if output.find(', not stripped') < 0:
        raise Exception("expected " + nonStrippedFile + " to be stripped, but its not: " + output)

print("All files OK")
