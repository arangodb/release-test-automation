
Dependencies
------------
- python 3
- python requests to talk to the instances https://requests.readthedocs.io/en/latest/
- Python expect - https://github.com/pexpect/pexpect https://pexpect.readthedocs.io/en/stable/ (debian only)
- PS-util  https://psutil.readthedocs.io/en/latest/#windows-services on windows `_pswindows.py` needs to be copied 
 into the python installation after the pip run: 
   - python install root (i.e. Users/willi/AppData/Local/Programs/Python)
   -  /Python38-32/Lib/site-packages/psutil/_pswindows.py
 the upstream distribution doesn't enable the wrappers to start/stop service 
- pyyaml - for parsing saved data.
- click - for commandline parsing https://click.palletsprojects.com/en/7.x/

`pip3 install psutil pyyaml pexpect requests click`

Using
-----

Parameter:
 - `--version` which Arangodb Version you want to run the test on
 - `--enterprise` whether its an enterprise or community package you want to install
 - `--packageDir` The directory where you downloaded the nsis .exe / deb [/ rpm TODO]
 - `--mode [_all_|install|uninstall|tests]` 
   - `all` (default) is intended to run the full flow. This is the production flow.
   - `install` to only install the package onto the system and store its setting to the temp folder (development) 
   - `tests`  to read the config file from the temp folder and run the tetss. 
   - `uninstall` to clean up your system.

Example usage:
 - Windows: `python ./release_tester/test.py --version 3.6.2 --enterprise True --package-dir c:/Users/willi/Downloads `
 - Linux (ubuntu|debian) `python3 ./release_tester/test.py --version 3.6.2 --enterprise True --package-dir /home/willi/Downloads`
 - Linux (centos|fedora|sles) TODO

Source distribution
-------------------
 - `release_tester/test.py` - main process flow, install, run test, uninstall
 - `release_tester/installers/installer.py` distribuiton / OS specific [un]installation automation
 - `release_tester/startermanager.py` manage one starter instance and get information about its launched processes
 - `release_tester/installers/arangodlog.py` arangod log examining to detect PID, `ready for business`-helo, leadership takeover. 
 - `release_tester/installers/arangosh.py` launch an arangosh with javascript snippets against the starter installation
 - `release_tester/installers/starterenvironment.py` set up one of [Leader/Follower | Active Failover | Cluster | DC2DC]
 
 - `attic_snippets` - trial and error scripts of start phase, to be deleted at some time.
GOAL
====
create most of the flow of i.e. https://github.com/arangodb/release-qa/issues/264 in a portable way. 









Structure going to become:
https://docs.python-guide.org/writing/structure/


attic_snippets/ contains examples and development test code 
