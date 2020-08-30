# Dependencies

- python 3
- python requests to talk to the instances https://requests.readthedocs.io/en/latest/
- Python expect - https://github.com/pexpect/pexpect https://pexpect.readthedocs.io/en/stable/ (linux only)
- PS-util  https://psutil.readthedocs.io/en/latest/#windows-services on windows `_pswindows.py` needs to be copied
 into the python installation after the pip run:
   - python install root (i.e. Users/willi/AppData/Local/Programs/Python)
   -  /Python38-32/Lib/site-packages/psutil/_pswindows.py
 the upstream distribution doesn't enable the wrappers to start/stop service
- pyyaml - for parsing saved data.
- click - for commandline parsing https://click.palletsprojects.com/en/7.x/
- semver - semantic versioning.
- gdb - for checking debug symbol. `sudo apt-get install gdb` macos:`brew install gdb` 

# Installing

## Linux

- **debian** / **ubuntu**:
  `apt-get install python3-yaml python3-requests python3-click python3-distro python3-psutil python3-pexpect python3-pyftpdlib`
  the `python3-semver` on debian is to old - need to use the pip version instead: `pip3 install semver` `apt-get install gdb`
- **centos**:
   `yum update ; yum install python3 python3-pyyaml python36-PyYAML python3-requests python3-click gcc platform-python-devel python3-distro python3-devel python36-distro python36-click python36-pexpect python3-pexpect python3-pyftpdlib; pip3 install psutil semver` 
   `sudo yum install gdb`
- **plain pip**:
  `pip3 install psutil pyyaml pexpect requests click semver ftplib` 

## Mac OS
:
    `brew install gnu-tar`
    `pip3 install click psutil requests pyyaml semver pexpect ftplib`
    `brew install gdb`

## Windows

TBD

# specifying versions

https://python-semver.readthedocs.io/ is used for version handling. hence the syntax for versions is:

`3.7.1-rc.1+0.501` where `0.501` is the package version that we add in .rpm
`3.7.1` will download the final release packages.

# Using test.py for release testing

test.py is intended to test the flow
 - install package
 - run starter tests
 - uninstall package

This sequence can be broken up by invoking test.py with `--mode install` and subsequently multiple invokactions with `--mode tests`. The system can afterwards be cleaned with `--mode uninstall`. 
For this, a setting file `/tmp/config.yml` is kept. This way parts of this flow can be better tuned without the resource intense un/install process.

Supported Parameters:
 - `--version` which Arangodb Version you want to run the test on
 - `--[no-]enterprise` whether its an enterprise or community package you want to install Specify for enterprise, ommit for community.
 - `--zip` switches from system packages to the tar.gz/zip package for the respective platform.
 - `--package-dir` The directory where you downloaded the nsis .exe / deb / rpm [/ dmg WIP]
 - `--[no-]interactive` (false if not invoked through a tty) whether at some point the execution should be paused for the user to execute manual tests with provided the SUT
 - `--mode [_all_|install|uninstall|tests]`
   - `all` (default) is intended to run the full flow. This is the production flow.
   - `install` to only install the package onto the system and store its setting to the temp folder (development) 
   - `tests`  to read the config file from the temp folder and run the tetss.
   - `uninstall` to clean up your system.
 - `--starter-mode [all|LF|AFO|CL|DC|none]` which starter test to exute, `all` of them or `none` at all or: 
   - `LF` - Leader / Follower - setup two single instances, start replication between them
   - `AFO` - Active Failover - start the agency and servers for active failover, test failovers, leader changes etc.
   - `CL` - Cluster - start a cluster with 3 agents, 3 db-servers, 3 coordinators. Test stopping one. 
   - `DC` - setup 2 clusters, connect them with arangosync (enterprise only)
 - `--publicip` the IP of your system - used instead of `localhost` to compose the interacitve URLs.
 - `--verbose` if specified more logging is done

Example usage:
 - Windows: `python ./release_tester/test.py --version 3.6.2 --enterprise --package-dir c:/Users/willi/Downloads `
 - Linux (ubuntu|debian) `python3 ./release_tester/test.py --version 3.6.2 --no-enterprise --package-dir /home/willi/Downloads`
 - Linux (centos|fedora|sles) `python3 ./release_tester/test.py --version 3.6.2 --enterprise --package-dir /home/willi/Downloads`

# Using upgrade.py for upgrade testing

upgrade.py is intended to test the flow
 - install old package
 - setup one starter test
 - upgrade package
 - upgrade starter environment
 - run tests


Supported Parameters:
 - `--old-version` which Arangodb Version you want to install to setup the old system
 - `--version` which Arangodb Version you want to upgrade the environment to
 - `--zip` switches from system packages to the tar.gz/zip package for the respective platform.
 - `--[no-]enterprise` whether its an enterprise or community package you want to install Specify for enterprise, ommit for community.
 - `--package-dir` The directory where you downloaded the nsis .exe / deb / rpm [/ dmg WIP]
 - `--[no-]interactive` (false if not invoked through a tty) whether at some point the execution should be paused for the user to execute manual tests with provided the SUT
 - `--publicip` the IP of your system - used instead of `localhost` to compose the interacitve URLs.
 - `--verbose` if specified more logging is done
 - `--starter-mode [all|LF|AFO|CL|DC|none]` which starter test to exute, `all` of them or `none` at all or: 
   - `LF` - Leader / Follower - setup two single instances, start replication between them
   - `AFO` - Active Failover - start the agency and servers for active failover, test failovers, leader changes etc.
   - `CL` - Cluster - start a cluster with 3 agents, 3 db-servers, 3 coordinators. Test stopping one. 
   - `DC` - setup 2 clusters, connect them with arangosync (enterprise only)

Example usage:
 - Windows: `python ./release_tester/upgrade.py --old-version 3.5.4 --version 3.6.2 --enterprise --package-dir c:/Users/willi/Downloads `
 - Linux (ubuntu|debian) `python3 ./release_tester/upgrade.py --old-version 3.5.4 --version 3.6.2 --enterprise --package-dir /home/willi/Downloads`
 - Linux (centos|fedora|sles) `python3 ./release_tester/upgrade.py --old-version 3.5.4 --version 3.6.2 --enterprise --package-dir /home/willi/Downloads`

# using acquire_packages.py to download packages from stage1/stage2/live

acquire_packages.py can fetch a set of packages for later use with upgrade.py/test.py. It will detect the platform its working on.

Supported Parameters:
 - `--version` which Arangodb Version you want to run the test on
 - `--[no-]enterprise` whether its an enterprise or community package you want to install Specify for enterprise, ommit for community.
 - `--enterprise-magic` specify your secret enterprise download key here.
 - `--zip` switches from system packages to the tar.gz/zip package for the respective platform.
 - `--package-dir` The directory where we will download the nsis .exe / deb / rpm [/ dmg WIP] to
 - `--source [public|[ftp|http]:stage1|[ftp|http]:stage2]`
   - `public` (default) will download the packages from downloads.arangodb.com
   - `stage1` will download the files from the staging fileserver - level 1 - ftp: internal http external requires credentials
   - `stage2` will download the files from the staging fileserver - level 2 - ftp: internal http external requires credentials
 - `--httpuser` username for stage http access
 - `--httppassvoid` secret for stage http access
 - `--verbose` if specified more logging is done
 - `--force` overwrite readily existing downloaded packages

example usage:
`python3 release_tester/acquire_packages.py --enterprise --version '3.7.1-rc.1+0.501' --enterprise-magic <enterprisekey> --package-dir /home/willi/Downloads/ --force --source ftp:stage2`

# Using cleanup.py to clean out the system

`cleanup.py` will try to invoke all known cleanup mechanisms, to bring your system as much as possible into a 'pure' state.

 - `--zip` switches from system packages to the tar.gz/zip package for the cleanup.

# Source distribution

- `release_tester/test.py` - main process flow, install, run test, uninstall
 - `release_tester/upgrade.py` - main upgrade process flow, install, run test, upgrade, test again, uninstall
 - `release_tester/installers/[base|nsis|deb|rpm|mac].py` distribuiton / OS specific [un]installation automation
 - `release_tester/arangodb/log.py` arangod log examining to detect PID, `ready for business`-helo, leadership takeover. 
 - `release_tester/arangodb/sh.py` launch an arangosh with javascript snippets against the starter installation
 - `release_tester/arangodb/sync.py` manage arangosync invocations
 - `release_tester/arangodb/starter/manager.py` manage one starter instance and get information about its launched processes
 - `release_tester/arangodb/starter/environment/[runner|leaderfolower|cluster|activefailover|dc2dc].py` set up one of [Leader/Follower | Active Failover | Cluster | DC2DC]
 - `release_tester/tools` several utility functions
 - `test_data` - the famous makedata suite
 - `attic_snippets` - trial and error scripts of start phase, utility functions like killall for mac/windows for manual invocation


# GOAL

create most of the flow of i.e. https://github.com/arangodb/release-qa/issues/264 in a portable way. 

### CI mode
- invoke testing.js
- run several threads with tests
python3 release_tester/ci.py --source-dir /home/willi/src/devel/ --build-dir build  --version 3.8.0-devel
