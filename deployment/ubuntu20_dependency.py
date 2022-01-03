#!/usr/bin/env python3
import os
import subprocess
from subprocess import STDOUT
import shutil
import time
import shlex
from pathlib import Path

"""
Goal:
    1. install python3 on current OS (latest version preferable, at least v3.6+)
    2. check and install all the dependecy library for the release-test-automation for QA testing
"""


"""
Special requirement: 
    1. in order get latest ppa and install 3.6-dev need to run manually as it need manual interaction
        -sudo add-apt-repository ppa:deadsnakes/ppa
"""

"""
In order to have clean environment
    dpkg --list | grep arango
    sudo apt-get purge --auto-remove arangodb3
    sudo apt-get auto-remove gdb -y
    sudo -H python3.6 -m pip uninstall pyftpdlib -y
    sudo -H python3.6 -m pip uninstall pipreqs -y
    sudo python3.6 -m pip uninstall -r /home/fattah/Downloads/release-test-automation-master/requirements.txt -y
    sudo apt-get autoremove python3.6
"""


# Updating current repository
print("Updating current repository")
cmd1 = ["apt-get", "update", "-y"]
proc = subprocess.Popen(cmd1, bufsize=-1, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
proc.communicate()
proc.wait()
time.sleep(2)


# Installing Python3.6-dev
print("\nInstalling python3.6-dev.\n")
cmd2 = ["apt-get", "install", "-y", "python3.8-dev"]
proc = subprocess.Popen(cmd2, bufsize=-1, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


# Installing gdb
print("\nInstalling GDB")
cmd3 = ["sudo", "apt", "-y", "install", "gdb"]
proc = subprocess.Popen(cmd3, bufsize=-1, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


# Installing Python3-pip
print("\nInstalling Python3-pip")
cmd4 = ["apt", "install", "python3-pip", "-y"]
proc = subprocess.Popen(cmd4, bufsize=-1, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


# Upgrading pip3 version if necessary
# print('\nUpgrading pip3 version')
# cmd5 = ['python3.6', '-m', 'pip', 'install', '--upgrade', 'pip']
# proc = subprocess.Popen(cmd5, bufsize=-1,
#                         stderr=subprocess.PIPE,
#                         stdin=subprocess.PIPE)
# proc.communicate()
# proc.wait()


print("\nInstalling pipreqs")
cmd6 = ["sudo", "-H", "python3.8", "-m", "pip", "install", "pipreqs"]
proc = subprocess.Popen(cmd6, bufsize=-1, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
proc.communicate()
proc.wait()

pwd = os.path.dirname(os.path.realpath(__file__))

# run pepreqs on project folder & it will create the requirement.txt file
print("\nRunning pepreqs on project folder.\n")
cmd7 = ["pipreqs", Path(pwd, "..")]
proc = subprocess.Popen(cmd7, bufsize=-1, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


# run pip3 install on requirement.txt file
path = pwd + "/../requirements.txt"
print("\nInstalling all dependency packages for release-test-automation.\n")
cmd8 = ["sudo", "-H", "python3.8", "-m", "pip", "install", "-r", path]
proc = subprocess.Popen(cmd8, bufsize=-1, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


# Installing pyftpdlib package
print("\nInstalling pyftpdlib package.\n")
cmd9 = ["sudo", "-H", "python3.8", "-m", "pip", "install", "pyftpdlib"]
proc = subprocess.Popen(cmd9, bufsize=-1, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


print("\nCurrent Python3 Version ")
cmd0 = ["python3.8", "-V"]
proc = subprocess.Popen(cmd0, bufsize=-1, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


print("\nCurrent GDB Version ")
cmd01 = ["gdb", "--version"]
proc = subprocess.Popen(cmd01, bufsize=-1, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


shutil.copyfile(
    pwd + "/../jenkins/jenkins-release-test-automation-sudoers",
    "/etc/sudoers.d/jenkins-release-test-automation",
)

print("\nAll dependency has been configured & and ready to run release-test-automation.")
