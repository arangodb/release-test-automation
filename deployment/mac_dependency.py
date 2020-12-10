#!/usr/bin/env python3
import os
import subprocess
import shutil
import time


"""
Goal:
    1. install python3 on current OS (latest version preferable, at least v3.6+)
    2. check and install all the dependecy library for the release-test-automation for QA testing
"""


"""
Special requirement:
    1.
"""

"""
In order to have clean environment
    sudo -H python3 -m pip uninstall pyftpdlib -y
    sudo -H python3 -m pip uninstall pipreqs -y
    sudo -H python3 -m pip uninstall -r /home/fattah/Downloads/release-test-automation-master/requirements.txt -y
"""

# Reseting Homebrew
print('Resetting Homebrew')
cmd1 = ['brew', 'update-reset']
proc = subprocess.Popen(cmd1, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
output, error = proc.communicate()
print(error)
proc.wait()
time.sleep(2)


# Updating current homebrew
print('Updating current repository')
cmd2 = ['brew', 'update']
proc = subprocess.Popen(cmd2, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
proc.communicate()
print(error)
proc.wait()
time.sleep(2)


# Updating current homebrew repository
print('Upgrading homebrew packages')
cmd3 = ['brew', 'upgrade']
proc = subprocess.Popen(cmd3, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
proc.communicate()
print(error)
proc.wait()
time.sleep(2)


# Installing Python3 latest version
print('\nInstalling latest python3 \n')
cmd4 = ['brew', 'install', 'python@3.9']
proc = subprocess.Popen(cmd4, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
output, error = proc.communicate()
print(error)
proc.wait()
time.sleep(2)


# downloading Pip3 latest version
print('\nInstalling latest pip3 \n')
cmd5 = ['curl', '-O', 'https://bootstrap.pypa.io/get-pip.py']
proc = subprocess.Popen(cmd5, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
output, error = proc.communicate()
print(error)
proc.wait()
time.sleep(2)


# Installing Pip3 latest version
cmd6 = ['sudo', '-H', 'python3', 'get-pip.py']
proc = subprocess.Popen(cmd6, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
output, error = proc.communicate()
print(error)
proc.wait()
time.sleep(2)



# Installing gdb latest version
print('\nInstalling latest gdb version \n')
cmd7 = ['brew', 'install', 'gdb']
proc = subprocess.Popen(cmd7, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
output, error = proc.communicate()
print(error)
proc.wait()
time.sleep(2)


# Installing pipreqs latest version
cmd8 = ['sudo', '-H', 'python3', '-m', 'pip', 'install', 'pipreqs']
proc = subprocess.Popen(cmd8, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
output, error = proc.communicate()
print(error)
proc.wait()
time.sleep(2)


path = raw_input("\nEnter the path of release-test-automation directory: ")
# run pepreqs on project folder & it will create the requirement.txt file
print('\nRunning pepreqs on project folder.\n')
cmd9 = ['pipreqs', path]
proc = subprocess.Popen(cmd9, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
output, error = proc.communicate()
print(error)
proc.wait()
time.sleep(2)


# run pip3 on requirement.txt file
path = path + '/requirements.txt'
print('\nInstalling all dependency packages for release-test-automation.\n')
cmd01 = ['sudo', '-H', 'python3', '-m', 'pip', 'install', '-r', path]
proc = subprocess.Popen(cmd01, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
output, error = proc.communicate()
print(error)
proc.wait()
time.sleep(2)


# Installing pyftpdlib package 
print('\nInstalling pyftpdlib package.\n')
cmd02 = ['sudo', '-H', 'python3', '-m', 'pip', 'install', 'pyftpdlib']
proc = subprocess.Popen(cmd02, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
output, error = proc.communicate()
print(error)
proc.wait()
time.sleep(2)


print('\nCurrent Python3 Version ')
cmd0 = ['python3', '-V']
proc = subprocess.Popen(cmd0, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
output, error = proc.communicate()
print(error)
proc.wait()
time.sleep(2)



print('\nCurrent GDB Version ')
cmd01 = ['gdb', '--version']
proc = subprocess.Popen(cmd01, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
output, error = proc.communicate()
print(error)
proc.wait()
time.sleep(2)

print('\nAll dependency has been configured & and ready to run release-test-automation.')
