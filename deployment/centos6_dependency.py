#!/usr/bin/env python3
import os
import subprocess
import shutil


"""
Goal:
    1. install python3 on current OS (latest version preferable, at least v3.6+ )
    2. check and install all the dependecy library for the release-test-automation for QA testing
"""

#checking for available python3 version
#yum search python3 | grep devel

# installing python3.6-devel yum install -y python3-devel.x86_64
print('installing python3.6\n')
cmd1 = ['yum', 'install', '-y', 'python36-devel.x86_64']
proc = subprocess.Popen(cmd1, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
proc.communicate()
proc.wait()

 
# installing CentOS SCLo RH repository for centos to install gdb yum install centos-release-scl-rh
print('installing centos-release-scl-rh repository\n')
cmd1 = ['yum', 'install', '-y', 'centos-release-scl-rh']
proc = subprocess.Popen(cmd1, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


# installing gdb yum install centos-release-scl-rh
print('installing devtoolset-9-gdb-gdbserver rpm package\n')
cmd1 = ['yum', 'install', '-y', 'devtoolset-9-gdb-gdbserver']
proc = subprocess.Popen(cmd1, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


# installing ftplib 
print('installing ftplib\n')
cmd1 = ['yum', 'install', 'ftplib']
proc = subprocess.Popen(cmd1, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


# pip3 install -U --user pipreqs for upgrade
print('Installing pipreqs.\n')
cmd1 = ['pip3', 'install', '--user', 'pipreqs']
proc = subprocess.Popen(cmd1, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


path = raw_input("\nEnter the path of release-test-automation directory: ")
# run pepreqs on project folder & it will create the requirement.txt file
print('\nRunning pepreqs on project folder.\n')
cmd2 = ['pipreqs', path]
proc = subprocess.Popen(cmd2, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
proc.communicate()
proc.wait()


path = path + '/requirements.txt'
# run pip3 install on requirement.txt file
print('\nInstalling all dependency packages for release-test-automation.\n')
cmd3 = ['pip3', 'install', '-r', path]
proc = subprocess.Popen(cmd3, bufsize=-1,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE)
proc.communicate()
proc.wait()

pwd = os.path.dirname(os.path.realpath(__file__))

shutil.copyfile(pwd + "/../jenkins/jenkins-release-test-automation-sudoers", "/etc/sudoers.d/jenkins-release-test-automation")
