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
    # print(l)
    return l

isEnterprise = sys.argv[1] == 'enterprise'

def isEnterpriseFile(fileToCheck):
    try:
        enterpriseBinaries.index(fileToCheck)
        return True
    except ValueError:
        return False

for symlink in installSymlinks:
    if isEnterpriseFile(symlink) and not isEnterprise:
        if os.path.exists(symlink):
            raise Exception('enterprise file found in community install!: ' + symlink)
        else:
            continue
    if not os.path.islink(symlink):
        raise Exception(" expected " + symlink + " to be a symlink ")

for strippedFile in installStrippedBinaries:
    if isEnterpriseFile(strippedFile) and not isEnterprise:
        if os.path.exists(strippedFile):
            raise Exception('enterprise file found in community install!: ' + strippedFile)
        else:
            continue
    output = runFileCommand(strippedFile)
    if output.find(', stripped') < 0:
        raise Exception("expected " + strippedFile + " to be stripped, but its not: " + output)

for nonStrippedFile in installNonStrippedBinaries:
    if isEnterpriseFile(nonStrippedFile) and not isEnterprise:
        if os.path.exists(nonStrippedFile):
            raise Exception('enterprise file found in community install!: ' + nonStrippedFile)
        else:
            continue
    output = runFileCommand(nonStrippedFile)
    if output.find(', not stripped') < 0:
        raise Exception("expected " + nonStrippedFile + " to be stripped, but its not: " + output)

print("All files OK")
