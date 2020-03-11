#!/usr/bin/python3
import os
import sys
import re
import subprocess


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

enterpriseBinaries = [
    '/usr/bin/arangobackup',# enterprise
    '/usr/bin/arangosync', # enterprise
    '/usr/sbin/rclone-arangodb'] # enterprise

def runFileCommand(fileToCheck):
    Popen=subprocess.Popen
    PIPE=subprocess.PIPE
    Popen=subprocess.Popen
    p = Popen(['file', fileToCheck], stdout=PIPE, stdin=PIPE, stderr=PIPE, universal_newlines=True)
    l = p.stdout.readline()
    print(l)
    return l

for symlink in installSymlinks:
    if not os.path.islink(symlink):
        raise Exception(" expected " + symlink + " to be a symlink ")

for strippedFile in installStrippedBinaries:
    output = runFileCommand(strippedFile)
    if output.find(', stripped') < 0:
        raise Exception("expected " + strippedFile + " to be stripped, but its not: " + output)

for nonStrippedFile in installNonStrippedBinaries:
    output = runFileCommand(nonStrippedFile)
    if output.find(', not stripped') < 0:
        raise Exception("expected " + nonStrippedFile + " to be stripped, but its not: " + output)

print("All files OK")
