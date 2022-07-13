# Dependencies

- python 3
- python requests to talk to the instances https://requests.readthedocs.io/en/latest/
- Python expect - https://github.com/pexpect/pexpect https://pexpect.readthedocs.io/en/stable/ (linux only)
- PS-util  https://psutil.readthedocs.io/en/latest/#windows-services 
- pyyaml - for parsing saved data.
- click - for commandline parsing https://click.palletsprojects.com/en/7.x/
- semver - semantic versioning.
- beautiful table - https://beautifultable.readthedocs.io/en/latest/quickstart.html
- certifi - to use custom SSL certificates with the python requests lib
- gdb - for checking debug symbol. `sudo apt-get install gdb` macos:`brew install gdb` 

# Installing

## Linux

- **debian** / **ubuntu**:
  `apt-get install python3-yaml python3-requests python3-click python3-distro python3-psutil python3-pexpect python3-pyftpdlib python3-statsd python3-selenium python3-pip gdb`
  
  the `python3-semver` on debian is to old - need to use the pip version instead:
  `pip3 install semver beautifultable allure_python_commons certifi tabulate`
  
  Ubuntu 16.40 pip3 system package is broken. Fix like this: 
  `dpkg -r python3-pip python3-pexpect` 
  `python3.8 -m easy_install pip`
  `pip install distro semver pexpect psutil beautifultable allure_python_commons certifi`
  
- **centos**:
   `yum update ; yum install python3 python3-pyyaml python36-PyYAML python3-requests python3-click gcc platform-python-devel python3-distro python3-devel python36-distro python36-click python36-pexpect python3-pexpect python3-pyftpdlib; pip3 install psutil semver beautifultable` 
   `sudo yum install gdb`
- **plain pip**:
  `pip3 install psutil pyyaml pexpect requests click semver ftplib selenium beautifultable tabulate allure_python_commons certifi`
  or:
  `pip install -r requirements.txt`

## Mac OS
:
    `brew install gnu-tar`
    `pip3 install click psutil requests pyyaml semver pexpect selenium beautifultable tabulate allure_python_commons certifi`
    `brew install gdb`
if `python --version` is below 3.9 you also have to download ftplib:
    `pip3 install click ftplib`

## Selenium dependencies
### chrome
If your system already has a chrome / chromium the [chromedriver](https://chromedriver.chromium.org/downloads) matching your browser version has to be installed

Typical arguments that may make chrome work:

    --selenium Chrome
    --selenium-driver-args headless
    --selenium-driver-args disable-dev-shm-usage
    --selenium-driver-args no-sandbox
    --selenium-driver-args remote-debugging-port=9222
    --selenium-driver-args start-maximized


## Windows

On Windows we require `PYTHONUTF8=1` in the OS-Environment in order to avoid non supported conversions in print statements.

  `pip install -r requirements.txt`

should be used to install the python dependencies.

# specifying versions

https://python-semver.readthedocs.io/ is used for version handling. hence the syntax for versions is:

`3.7.1-rc.1+0.501` where `0.501` is the package version that we add in .rpm
`3.7.1` will download the final release packages.

# Using `test.py` for release testing

`test.py` is intended to test the flow
 - install package
 - run starter tests
 - uninstall package

This sequence can be broken up by invoking `test.py` with `--mode install` and subsequently multiple invokactions with `--mode tests`. The system can afterwards be cleaned with `--mode uninstall`. 
For this, a setting file `/tmp/config.yml` is kept. This way parts of this flow can be better tuned without the resource intense un/install process.

Supported Parameters:
 - `--new-version` which Arangodb Version you want to run the test on
 - `--[no-]enterprise` whether its an enterprise or community package you want to install Specify for enterprise, ommit for community.
 - `--[no-]encryption-at-rest` turn on encryption at rest for Enterprise packages
 - `--zip` switches from system packages to the tar.gz/zip package for the respective platform.
 - `--src` switches to [Source directory](#source-installer) logic
 - `--package-dir` The directory where you downloaded the nsis .exe / deb / rpm [/ dmg WIP]
 - `--[no-]interactive` (false if not invoked through a tty) whether at some point the execution should be paused for the user to execute manual tests with provided the SUT
 - `--test-data-dir` - the base directory where the tests starter instances should be created in (defaults to `/tmp/`)
 - `--mode [_all_|install|uninstall|tests]`
   - `all` (default) is intended to run the full flow. This is the production flow.
   - `install` to only install the package onto the system and store its setting to the temp folder (development) 
   - `tests`  to read the config file from the temp folder and run the tetss.
   - `uninstall` to clean up your system.
 - `--starter-mode [all|LF|AFO|CL|DC|DCendurance|none]` which starter test to exute, `all` of them or `none` at all or:
   - `LF` - Leader / Follower - setup two single instances, start replication between them
   - `AFO` - Active Failover - start the agency and servers for active failover, test failovers, leader changes etc.
   - `CL` - Cluster - start a cluster with 3 agents, 3 db-servers, 3 coordinators. Test stopping one. 
   - `DC` - setup 2 clusters, connect them with arangosync (enterprise only)
   - `DCendurance` - use DC setup to launch long running arangobenches (not part of `all`)
 - `--publicip` the IP of your system - used instead of `localhost` to compose the interacitve URLs.
 - `--verbose` if specified more logging is done
 - `--selenium` - specify the webdriver to be used to work with selenium (if)
 - `--selenium-driver-args` - arguments to the selenium browser - like `headless`
 - `--alluredir` - directory to save test results in allure format (default = allure-results)
 - `--clean-alluredir/--do-not-clean-alluredir` - clean allure directory before running tests (default = True)
 - `--[no-]ssl` use SSL (default = False)
 - `--use-auto-certs` use self-signed SSL certificates (only applicable when using --ssl) 
 - `--abort-on-error/--do-not-abort-on-error` - abort if one of the deployments failed
Example usage:
 - Windows: `python ./release_tester/test.py --new-version 3.6.2 --enterprise --package-dir c:/Users/willi/Downloads `
 - Linux (ubuntu|debian) `python3 ./release_tester/test.py --new-version 3.6.2 --no-enterprise --package-dir /home/willi/Downloads`
 - Linux (centos|fedora|sles) `python3 ./release_tester/test.py --new-version 3.6.2 --enterprise --package-dir /home/willi/Downloads`

# Using `upgrade.py` for upgrade testing

`upgrade.py` is intended to test the flow
 - install old package
 - setup one starter test
 - upgrade package
 - upgrade starter environment
 - run tests


Supported Parameters:
 - `--old-version` which Arangodb Version you want to install to setup the old system
 - `--new-version` which Arangodb Version you want to upgrade the environment to
 - `--zip` switches from system packages to the tar.gz/zip package for the respective platform.
 - `--src` switches to [Source directory](#source-installer) logic
 - `--[no-]enterprise` whether its an enterprise or community package you want to install Specify for enterprise, ommit for community.
 - `--[no-]encryption-at-rest` turn on encryption at rest for Enterprise packages
 - `--package-dir` The directory where you downloaded the nsis .exe / deb / rpm [/ dmg WIP]
 - `--[no-]interactive` (false if not invoked through a tty) whether at some point the execution should be paused for the user to execute manual tests with provided the SUT
 - `--test-data-dir` - the base directory where the tests starter instances should be created in (defaults to `/tmp/`)
 - `--publicip` the IP of your system - used instead of `localhost` to compose the interacitve URLs.
 - `--verbose` if specified more logging is done
 - `--starter-mode [all|LF|AFO|CL|DC|none]` which starter test to exute, `all` of them or `none` at all or: 
   - `LF` - Leader / Follower - setup two single instances, start replication between them
   - `AFO` - Active Failover - start the agency and servers for active failover, test failovers, leader changes etc.
   - `CL` - Cluster - start a cluster with 3 agents, 3 db-servers, 3 coordinators. Test stopping one. 
   - `DC` - setup 2 clusters, connect them with arangosync (enterprise only)
 - `--selenium` - specify the webdriver to be used to work with selenium (if)
 - `--selenium-driver-args` - arguments to the selenium browser - like `headless`
 - `--alluredir` - directory to save test results in allure format (default = allure-results)
 - `--clean-alluredir/--do-not-clean-alluredir` - clean allure directory before running tests (default = True)
 - `--[no-]ssl` use SSL (default = False)
 - `--use-auto-certs` use self-signed SSL certificates (only applicable when using --ssl)
 - `--abort-on-error/--do-not-abort-on-error` - abort if one of the deployments failed
 
Example usage:
 - Windows: `python ./release_tester/upgrade.py --old-version 3.5.4 --new-version 3.6.2 --enterprise --package-dir c:/Users/willi/Downloads `
 - Linux (ubuntu|debian) `python3 ./release_tester/upgrade.py --old-version 3.5.4 --new-version 3.6.2 --enterprise --package-dir /home/willi/Downloads`
 - Linux (centos|fedora|sles) `python3 ./release_tester/upgrade.py --old-version 3.5.4 --new-version 3.6.2 --enterprise --package-dir /home/willi/Downloads`

# Using `run_test_suites.py` to run test suites

This entrypoint file is used to run tests that are organized in test suites.
Supported Parameters:
 - `--include-test-suite` Test suite name to include in the test run. Multiple test suites can be ran by providing this parameter multiple times. This parameter cannot be used if --exclude-test-suite is set.
 - `--exclude-test-suite` Run all test suites except for this one. Multiple test suites can be excluded by providing this parameter multiple times. This parameter cannot be used if --include-test-suite is set.
 - `--new-version` which Arangodb Version you want to run the test on
 - `--old-version` old version of ArangoDB to be used in tests where an older version is required.
 - `--zip` switches from system packages to the tar.gz/zip package for the respective platform.
 - `--package-dir` The directory where you downloaded the nsis .exe / deb / rpm [/ dmg WIP]
 - `--[no-]interactive` (false if not invoked through a tty) whether at some point the execution should be paused for the user to execute manual tests with provided the SUT
 - `--verbose` if specified more logging is done
 - `--alluredir` - directory to save test results in allure format (default = allure-results)
 - `--clean-alluredir/--do-not-clean-alluredir` - clean allure directory before running tests (default = True)

Example usage:
 - Linux: `python3 ./release_tester/run_test_suites.py --new-version 3.10.0-nightly --old-version 3.9.1-nightly --verbose --no-enterprise --zip --package-dir /packages --include-test-suite EnterprisePackageInstallationTestSuite`

# Using `conflict_checking.py` for testing of package installation process

To run the tests you need to download older version packages in addition to the version you intend to test.
Both Community and Enterprise editions are required.   
Supported Parameters:
 - `--new-version` which Arangodb Version you want to run the test on
 - `--old-version` old version of ArangoDB to be used in tests where an older version is required, e.g. testing that newer debug package cannot be installed over older server package
 - `--[no-]enterprise` whether its an enterprise or community package you want to install Specify for enterprise, ommit for community.
 - `--package-dir` The directory where you downloaded the nsis .exe / deb / rpm [/ dmg WIP]
 - `--[no-]interactive` (false if not invoked through a tty) whether at some point the execution should be paused for the user to execute manual tests with provided the SUT
 - `--verbose` if specified more logging is done
 - `--alluredir` - directory to save test results in allure format (default = allure-results)
 - `--clean-alluredir/--do-not-clean-alluredir` - clean allure directory before running tests (default = True)

# Using `run_license_tests.py` to test the license manager feature

License manager tests are only applicable to enterprise edition.   
Supported Parameters:
 - `--new-version` which Arangodb Version you want to run the test on
 - `--package-dir` The directory where you downloaded the nsis .exe / deb / rpm [/ dmg WIP]
 - `--[no-]interactive` (false if not invoked through a tty) whether at some point the execution should be paused for the user to execute manual tests with provided the SUT
 - `--verbose` if specified more logging is done
 - `--alluredir` - directory to save test results in allure format (default = allure-results)
 - `--clean-alluredir/--do-not-clean-alluredir` - clean allure directory before running tests (default = True)
 - `--zip` switches from system packages to the tar.gz/zip package for the respective platform.

Example usage:
 - Linux (ubuntu|debian) `python3 ./release_tester/run_license_tests.py --new-version 3.9.0-nightly --verbose --package-dir /home/vitaly/tmp/packages --zip`

# using `download.py` to download packages from stage1/stage2/live

`download.py` can fetch a set of packages for later use with `upgrade.py`/`test.py`. It will detect the platform its working on.

Supported Parameters:
 - `--new-version` which Arangodb Version you want to run the test on
 - `--[no-]enterprise` whether its an enterprise or community package you want to install Specify for enterprise, ommit for community.
 - `--enterprise-magic` specify your secret enterprise download key here.
 - `--zip` switches from system packages to the tar.gz/zip package for the respective platform.
 - `--package-dir` The directory where we will download the nsis .exe / deb / rpm [/ dmg WIP] to
 - `--source [public|nightlypublic|[ftp|http]:stage1|[ftp|http]:stage2]`
   - `nightlypublic` will download the packages from the nightly builds at downloads.arangodb.com
   - `public` (default) will download the packages from downloads.arangodb.com
   - `stage1` will download the files from the staging fileserver - level 1 - ftp: internal http external requires credentials
   - `stage2` will download the files from the staging fileserver - level 2 - ftp: internal http external requires credentials
 - `--httpuser` username for stage http access
 - `--httppassvoid` secret for stage http access
 - `--verbose` if specified more logging is done
 - `--force` overwrite readily existing downloaded packages

example usage:
`python3 release_tester/download.py --enterprise \
                                    --new-version '3.7.1-rc.1+0.501' \
                                    --enterprise-magic <enterprisekey> \
                                    --package-dir /home/willi/Downloads/ \
                                    --force \
                                    --source ftp:stage2`

# Using `full_download_upgrade.py` for automated upgrade testing

`full_download_upgrade.py` integrates `upgrade.py` and `download_packages.py`.
It will download `Enterprise` and `Community` packages, while `-nightly` will first attempt
to resolve the proper version of the nightly package, since `-nightly` allways is a suffix to the latest released version + 1.

It will then run the `upgrade.py` mechanic for:
 - enterprise with encryption at rest enabled
 - enterprise 
 - community

and create a final report at the end of the run.

The downloading of packages can be circumvented by specifying `--source local`.

Supported Parameters:
 - `--[new|old]-version`
   - old: which Arangodb Version you want to install to setup the old system
   - new: which Arangodb Version you want to upgrade the environment to
 - `--zip` switches from system packages to the tar.gz/zip package for the respective platform.
 - `--[no-]enterprise` whether its an enterprise or community package you want to install Specify for enterprise, ommit for community.
 - `--[no-]encryption-at-rest` turn on encryption at rest for Enterprise packages
 - `--package-dir` The directory where you downloaded the nsis .exe / deb / rpm [/ dmg WIP]
 - `--enterprise-magic` specify your secret enterprise download key here.
 - `--[new|old]-source [public|nightlypublic|[ftp|http]:stage1|[ftp|http]:stage2]`
   - `nightlypublic` will download the packages from the nightly builds at downloads.arangodb.com
   - `local` no packages will be downloaded at all, but rather are expected to be found in `package-dir`.
   - `public` (default) will download the packages from downloads.arangodb.com
   - `stage1` will download the files from the staging fileserver - level 1 - ftp: internal http external requires credentials
   - `stage2` will download the files from the staging fileserver - level 2 - ftp: internal http external requires credentials
 - `--httpuser` username for stage http access
 - `--httppassvoid` secret for stage http access
 - `--force` overwrite readily existing downloaded packages
 - `--[no-]interactive` (false if not invoked through a tty) whether at some point the execution should be paused for the user to execute manual tests with provided the SUT
 - `--test-data-dir` - the base directory where the tests starter instances should be created in (defaults to `/tmp/`)
 - `--publicip` the IP of your system - used instead of `localhost` to compose the interacitve URLs.
 - `--verbose` if specified more logging is done
 - `--starter-mode [all|LF|AFO|CL|DC|none]` which starter test to exute, `all` of them or `none` at all or: 
   - `LF` - Leader / Follower - setup two single instances, start replication between them
   - `AFO` - Active Failover - start the agency and servers for active failover, test failovers, leader changes etc.
   - `CL` - Cluster - start a cluster with 3 agents, 3 db-servers, 3 coordinators. Test stopping one. 
   - `DC` - setup 2 clusters, connect them with arangosync (enterprise only)
 - `edition` which type to launch:
   - `C` community
   - `EP` enterprise
   - `EE` enterprise with encryption at rest
 - `--selenium` - specify the webdriver to be used to work with selenium (if)
 - `--selenium-driver-args` - arguments to the selenium browser - like `headless`
 - `--alluredir` - directory to save test results in allure format (default = allure-results)
 - `--clean-alluredir/--do-not-clean-alluredir` - clean allure directory before running tests (default = True)
 - `--[no-]ssl` use SSL (default = False)
 - `--use-auto-certs` use self-signed SSL certificates (only applicable when using --ssl)
 - `--abort-on-error/--do-not-abort-on-error` - abort if one of the deployments failed

Example usage: 

- [jenkins/nightly_tar.sh](jenkins/nightly_tar.sh) Download nightly tarball packages, and run it with selenium in `containers/docker_tar` ubuntu container
- [jenkins/nightly_deb.sh](jenkins/nightly_deb.sh) Download nightly debian packages, and run them with selenium in `containers/docker_deb` ubuntu container
- [jenkins/nightly_rpm.sh](jenkins/nightly_rpm.sh) Download nightly redhat packages, and run them with selenium in `containers/docker_rpm` centos 7 container


# Using `full_download_upgrade_test.py` for automated full release testing

`full_download_upgrade_test.py` integrates `test.py`, `upgrade.py` and `download_packages.py`.
It will download `Enterprise` and `Community` packages, while `-nightly` will first attempt
to resolve the proper version of the nightly package, since `-nightly` allways is a suffix to the latest released version + 1.



It will then run the `upgrade.py` mechanic for:
 - enterprise with encryption at rest enabled
 - enterprise 
 - community

and create a final report at the end of the run.

The downloading of packages can be circumvented by specifying `--source local`.

Supported Parameters:
 - `--new-version`
   - new: This is the to be released version. it will be downloaded from `--source`.
 - `--upgrade-matrix list` specify a list of upgrades to run. For all other versions, `--other-source` will
   be used to specify the download source. The list is specified in the format of: (without blanks)
     `first-From : first-To ; second-From : second-To`
 - `--zip` switches from system packages to the tar.gz/zip package for the respective platform.
 - `--package-dir` The directory where you downloaded the nsis .exe / deb / rpm [/ dmg WIP]
 - `--enterprise-magic` specify your secret enterprise download key here.
 - `--[other-]source [public|nightlypublic|[ftp|http]:stage1|[ftp|http]:stage2]`
   - `nightlypublic` will download the packages from the nightly builds at downloads.arangodb.com
   - `local` no packages will be downloaded at all, but rather are expected to be found in `package-dir`.
   - `public` (default) will download the packages from downloads.arangodb.com
   - `stage1` will download the files from the staging fileserver - level 1 - ftp: internal http external requires credentials
   - `stage2` will download the files from the staging fileserver - level 2 - ftp: internal http external requires credentials
 - `--httpuser` username for stage http access
 - `--httppassvoid` secret for stage http access
 - `--force` overwrite readily existing downloaded packages
 - `--test-data-dir` - the base directory where the tests starter instances should be created in (defaults to `/tmp/`)
 - `--publicip` the IP of your system - used instead of `localhost` to compose the interacitve URLs.
 - `--verbose` if specified more logging is done
 - `--starter-mode [all|LF|AFO|CL|DC|none]` which starter test to exute, `all` of them or `none` at all or: 
   - `LF` - Leader / Follower - setup two single instances, start replication between them
   - `AFO` - Active Failover - start the agency and servers for active failover, test failovers, leader changes etc.
   - `CL` - Cluster - start a cluster with 3 agents, 3 db-servers, 3 coordinators. Test stopping one. 
   - `DC` - setup 2 clusters, connect them with arangosync (enterprise only)
 - `edition` which type to launch:
   - `C` community
   - `EP` enterprise
   - `EE` enterprise with encryption at rest
 - `--selenium` - specify the webdriver to be used to work with selenium (if)
 - `--selenium-driver-args` - arguments to the selenium browser - like `headless`
 - `--alluredir` - directory to save test results in allure format (default = allure-results)
 - `--clean-alluredir/--do-not-clean-alluredir` - clean allure directory before running tests (default = True)
 - `--[no-]ssl` use SSL (default = False)
 - `--use-auto-certs` use self-signed SSL certificates (only applicable when using --ssl)
 - `--abort-on-error/--do-not-abort-on-error` - abort if one of the deployments failed
Example usage: 

- [jenkins/nightly_tar.sh](jenkins/nightly_tar.sh) Download nightly tarball packages, and run it with selenium in `containers/docker_tar` ubuntu container
- [jenkins/nightly_deb.sh](jenkins/nightly_deb.sh) Download nightly debian packages, and run them with selenium in `containers/docker_deb` ubuntu container
- [jenkins/nightly_rpm.sh](jenkins/nightly_rpm.sh) Download nightly redhat packages, and run them with selenium in `containers/docker_rpm` centos 7 container


# Using cleanup.py to clean out the system

`cleanup.py` will try to invoke all known cleanup mechanisms, to bring your system as much as possible into a 'pure' state.

 - `--zip` switches from system packages to the tar.gz/zip package for the cleanup.


# Using `deployment` scripts to install all the necessary dependency packages for testsystems
The scripts in the `deployment` directory will try to install all the required pacakges to a new/fresh machine in order to run release-test-automation tests.

`[centos6] || [ubuntu16].py`

# binaries strip cheking

 - Linux (ubuntu|debian|centos|fedora|sles)[deb|rpm|tar.gz] full support.
 - Mac [dmg|tar.gz] support through resource intense copy & compare; GO binaries such as `arangodb` and `arangosync` are assumed not to be stripped, since the mac strip command will fail for them.
 - Windows no supported yet.

# Source distribution

 - `release_tester/test.py` - main process flow, install, run test, uninstall
 - `release_tester/upgrade.py` - main upgrade process flow, install, run test, upgrade, test again, uninstall
 - `release_tester/download.py` - download packages via our various distribution routes
 - `release_tester/cleanup.py` - remove files and installed packages etc.
 - `release_tester/installers/[base|nsis|tar|linux|deb|rpm|mac].py` distribution / OS specific [un]installation/upgrade automation
 - `release_tester/arangodb/instance.py` wraps one process of arangod / arangosync; detects its operation mode
 - `release_tester/arangodb/sh.py` launch an arangosh with javascript snippets against the starter installation
 - `release_tester/arangodb/sync.py` manage arangosync invocations
 - `release_tester/arangodb/backup.py` manage arangobackup invocations
 - `release_tester/arangodb/starter/manager.py` manage one starter instance and get information about its launched processes
 - `release_tester/arangodb/starter/deployments/[runner|leaderfolower|activefailover|cluster|cluster_perf|dc2dc|dc2dcendurance].py` set up one of [Leader/Follower | Active Failover | Cluster Cluster_Perf | DC2DC | DCendurance]
 - `release_tester/tools` several utility functions
 - `test_data` - the famous makedata suite
 - `attic_snippets` - trial and error scripts of start phase, utility functions like killall for mac/windows for manual invocation


# makedata / checkdata framework
Makedata is ran inside arangosh. It was made to be user-expandeable by hooking in on test cases.
It consists of these files in test_data:
 - `makedata.js` - initially generate test data
 - `checkdata.js` - check whether data is available; could be read-only
 - `cleardata.js` - remove the testdata - after invoking it makedata should be able to be ran again without issues.
 - Plugins in `test_data/makedata_suites` executed in alphanumeric order:
   - `000_dummy.js` - this can be used as a template if you want to create a new plugin. 
   - `010_disabled_uuid_check.js` If you're running a cluster setup in failover mode, this checks and waits for all shards have an available leader.
   - `020_foxx.js` Installs foxx, checks it. 
   - `050_database.js` creates databases for the test data.
   - `100_collections.js` creates a set of collections / indices
   - `400_views.js` creates some views
   - `500_community_graph.js` creates a community patent graph
   - `550_enterprise_graph.js` creates an enterprise patent graph
   - `560_smartgraph_validator.js` on top of the enterprise graph, this will check the integrity check of the server.
   - `900_oneshard.js` creates oneshard database and does stuff with it.
   - `607_analyzers.js` creates suported analyzers for 3.7.x version and check it's functionality.
      Added Analyzers: (documentation link: https://www.arangodb.com/docs/3.7/analyzers.html)
      - identity: An Analyzer applying the identity transformation, i.e. returning the input unmodified.
      - delimiter: An Analyzer capable of breaking up delimited text into tokens as per RFC 4180 (without starting new  records on newlines).
      - stem : An Analyzer capable of stemming the text, treated as a single token, for supported languages.
      - norm Upper : An Analyzer capable of normalizing the text, treated as a single token, i.e. case conversion and accent removal. This one will Convert input string to all upper-case characters.
      - norm Accent : This analyzer is capable of convert accented characters to their base characters.
      - ngram : An Analyzer capable of producing n-grams from a specified input in a range of min..max (inclusive). Can optionally preserve the original input.
      - n-Bigram Markers: This analyzer is a bigram Analyzer with preserveOriginal enabled and with start and stop markers.
      - text : An Analyzer capable of breaking up strings into individual words while also optionally filtering out stop-words, extracting word stems, applying case conversion and accent removal.
      - text Edge ngram: This analyzer is a custom text Analyzer with the edge n-grams feature and normalization enabled, stemming disabled and "the" defined as stop-word to exclude it.
   - `608_analyzers.js` creates suported analyzers for 3.8.x version and check it's functionality.
   - `609_analyzers.js` creates suported analyzers for 3.9.x version and check it's functionality.

It should be considered to provide a set of hooks (000_dummy.js can be considered being a template for this):

- Hook to check whether the environment will support your usecase [single/cluster deployment, Community/Enterprise, versions in test]
- Per Database loop Create / Check [readonly] / Delete handler
- Per Collection loop Create / Check [readonly] / Delete handler

The hook functions should respect their counter parameters, and use them in their respective reseource names.
Jslint should be used to check code validity.

The list of the hooks enabled for this very run of one of the tools is printed on startup for reference.

Makedata should be considered a framework for consistency checking in the following situations:
 - replication
 - hot backup
 - upgrade
 - dc2dc

The replication fuzzing test should be used to ensure the above with randomness added.

Makedata is by default ran with one dataset. However, it can also be used as load generator. 
For this case especialy, the counters have to be respected, so subsequent runs don't clash with earlier runs.
The provided dbCount / loopCount should be used in identifiers to ensure this.

To Aid development, the makedata framework can be launched from within the arangodb unittests, 
if this repository is checked out next to it:

``` bash
./scripts/unittest rta_makedata --extremeVerbosity true --cluster true --makedata_args:bigDoc true
```

# Hot backup settings
During the test scenarios hot backups will be created/restored and uploaded/downloaded to/from an external storage using the bundled rclone. 
RTA supports different types of external storage. By default the backups will be just copied to another directory using rclone. 
Other options include running minio(S3-compatible open-source storage) locally and uploading backups to a real cloud provider. 
This is controlled using the following command line parameters:
 - `--hb-mode` - Hot backup mode. Possible values: disabled, directory, s3bucket, googleCloudStorage, azureBlobStorage. 
 - `--hb-provider` - Cloud storage provider. Possible values for s3bucket: minio, aws, gce, azure.
 - `--hb-storage-path-prefix` - Subdirectory to store hot backups in cloud.
 - `--hb-aws-access-key-id` [env `AWS_ACCESS_KEY_ID`] - AWS access key id
 - `--hb-aws-secret-access-key` [env `AWS_SECRET_ACCESS_KEY`] - AWS secret access key
 - `--hb-aws-region` [env `AWS_REGION`] - AWS region
 - `--hb-aws-acl` [env `AWS_ACL`] - AWS ACL (default value: `private`)
 - `--hb-gce-service-account-credentials` - GCE service account credentials(JSON string).
 - `--hb-gce-service-account-file` - Path to a JSON file containing GCE service account credentials.
 - `--hb-gce-project-number` - GCE project ID.  
 - `--hb-azure-account` - Azure storage account.
 - `--hb-azure-key` - Azure storage account access key.   
 - `--hb-use-cloud-preset` (string) - Load saved hotbackup settings. To use this, create a file release_tester/tools/external_helpers/cloud_secrets.py. Inside this file define dict variables. The name of the variable is the name of the preset. The dict must contain all the hb parameters. If --hb-use-cloud-preset is set, then all other parameters which names start with hb- are ignored.
   Example of cloud_secrets.py: 
```python
aws = {
    "hb_storage_path_prefix": "/path/inside/bucket",
    "hb_mode": "s3bucket",
    "hb_provider": "aws",
    "hb_aws_access_key_id": "SECRET_KEY",
    "hb_aws_secret_access_key": "ACCESS_KEY",
    "hb_aws_region": "eu-central-1",
    "hb_aws_acl": "private",
}
```

Each cloud storage may also have some specific configuration parameters, which must be set as environment variables.



# Flow of testcases
The base flow lives in `runner.py`; special deployment specific implementations in the respective derivates. 
The Flow is as follows:

```
install
prepare and setup abstractions, starter managers, create certificates, ec. [starter_prepare_env[_impl]]
launch all the actual starter instances, wait for them to become alive [starter_run[_impl]]
finalize the setup like start sync'ing [finish_setup[_impl]]
[makedata]
[makedata check]
=> ask user to inspect the installation
if HotBackup capable:
  create backup
  create data, that will be gone after restoring
  list backups
  upload backup
  delete backup
  list backup to revalidate there is none
  restore backup
  [checkdata]
  create non-backup data again
if Update:
  manage packages (uninstall debug, install new, install new debug, test debug)
  upgrade the starter environment [upgrade_arangod_version[_impl]]
  [makedata check] after upgrade 
  if Hotbackup capable:
    list backups
    upload backup once more
    delete backup
    list & check its empty
    restore the backup
    validate post-backup data is gone again
  [makedata check]
test the setup [test_setup[_impl]]
[makedata check]
try to jam the setup [jam_setup[_impl]]
[makedata check]
shutdown the setup
uninstall packages
```

# GOAL

create most of the flow of i.e. https://github.com/arangodb/release-qa/issues/264 in a portable way. 
arangosync

# Selenium UI testing

## Developing

Launching selemium wich browser in UI mode is more easy with the zip/tar packages, since they don't require privileges to run, 
hence just the users regular session can be used.

- launch a SUT using i.e. `./release_tester/test.py --no-enterprise --new-version 3.8.0-nightly --package-dir /home/willi/Downloads/ --zip --interactive --starter-mode CL` - let it running at that state. 
- edit scripts use `./release_tester/test_selenium.py --old-version 3.8.0-nightly --new-version 3.9.0-nightly --selenium Chrome --starter-mode CL --zip` to check them against the instance running on the same machine. 

once the scriptlet does what you want, you can use commands like this to run the test:
-  `./release_tester/test.py --new-version 3.8.0-nightly --zip --no-interactive --starter-mode CL --selenium Chrome`
# Perf

# Using perf.py for performance testing

perf.py is intended to test the flow
 - install package (optional)
 - run starter cluster (optional)
 - nur cluster_perf.py
 - uninstall package (optional)

This sequence can be broken up by invoking perf.py with `--mode install` and subsequently multiple invokactions with `--mode tests`. The system can afterwards be cleaned with `--mode uninstall`.
For this, a setting file `/tmp/config.yml` is kept. This way parts of this flow can be better tuned without the resource intense un/install process.

Supported Parameters:
 - `--new-version` which Arangodb Version you want to run the test on
 - `--[no-]enterprise` whether its an enterprise or community package you want to install Specify for enterprise, ommit for community.
 - `--[no-]encryption-at-rest` turn on encryption at rest for Enterprise packages
 - `--zip` switches from system packages to the tar.gz/zip package for the respective platform.
 - `--package-dir` The directory where you downloaded the nsis .exe / deb / rpm [/ dmg WIP]
 - `--[no-]interactive` (false if not invoked through a tty) whether at some point the execution should be paused for the user to execute manual tests with provided the SUT
 - `--test-data-dir` - the base directory where the tests starter instances should be created in (defaults to `/tmp/`)
 - `--mode [_all_|install|uninstall|tests]`
   - `all` (default) is intended to run the full flow. This is the production flow.
   - `install` to only install the package onto the system and store its setting to the temp folder (development) 
   - `tests`  to read the config file from the temp folder and run the tetss.
   - `uninstall` to clean up your system.
 - `--starter-mode [none]` not used atm. only cluster_perf is used.
 - `--publicip` the IP of your system - used instead of `localhost` to compose the interacitve URLs.
 - `--verbose` if specified more logging is done

 - `--scenario` a Yaml file containing the setup of the makedata injector
 - `--frontends` may be specified several times, disables launchin own cluster instance. Configures remote instances instead.

Example usage:
 - run against self started instance: `python3 release_tester/perf.py  --new-version 3.7.3  --enterprise --package-dir /home/willi/Downloads  --zip --verbose --interactive --mode tests --scenario scenarios/c_cluster_x3.yml`
 - run against remote instance: `python3 release_tester/perf.py  --new-version 3.7.3  --enterprise --package-dir /home/willi/Downloads  --zip --verbose --interactive --mode tests --scenario scenarios/c_cluster_x3.yml --frontends tcp://192.168.10.11:8529 --frontends tcp://192.168.10.12:8529 --frontends tcp://192.168.10.13:8529`


# scenario yml file
They are kept in `scenarios/`. 

```
!!python/object:arangodb.starter.deployments.cluster_perf.testConfig
collection_multiplier: 1
data_multiplier: 4
db_count: 100
db_count_chunks: 10
max_replication_factor: 3
min_replication_factor: 2
parallelity: 9
launch_delay: 9.7
db_offset: 0
single_shard: false
```
 - `collection_multiplier`: how many more times should we create collections?
 - `data_multiplier`: how many more times should we create data inside the database?
 - `db_count`: how many databases should this instance of the test create
 - `db_count_chunks`: how many chunks of `db_count` do we want to create?
 - `db_offset`: should we start counting the database name at an offset?
 - `single_shard`: whether this is going to be a single shard or multi shard test
 - `max_replication_factor`: collections will have no more than this many shards
 - `min_replication_factor`: collections will have no less than this many shards
 - `parallelity`: how many parallel arangosh instances creating data should be spawned
 - `launch_delay`: wait this many seconds between launching two arangoshs to create an offset


# statsd integration
makedata values are pushed via statsd client via https://github.com/prometheus/statsd_exporter to prometheus.
adds the `python3-statsd` dependency.


connect statsd to prometheus:
```
  - job_name: statsd
    scrape_interval: 1s
    metrics_path: /metrics
    # bearer_token_file: /etc/prometheus/prometheus.token
    static_configs:
    - targets: ['localhost:9102']
```

Run the statsd exporter:
```
./statsd_exporter --statsd.listen-udp=:8125 --statsd.listen-tcp=:8125
```

# launching the tests

Running a full test with launching the system, waiting before the loadtest starts:

```
python3 release_tester/perf.py --new-version 3.7.3 \
                               --enterprise \
                               --package-dir /home/willi/Downloads \
                               --zip \
                               --test-data-dir /tmp/ \
                               --verbose \
                               --interactive
```

Running perf with a remote test system:

```
python3 release_tester/perf.py --new-version 3.7.3
                               --enterprise \
                               --package-dir /home/willi/Downloads \
                               --zip \
                               --frontends tcp://192.168.173.88:9729 \
                               --frontends tcp://192.168.173.88:9529 \
                               --frontends tcp://192.168.173.88:9629 \
                               --mode tests \
                               --verbose \
                               --scenario scenarios/cluster_replicated.yml
```

# docker container
We will build a the docker container based on the latest public enterprise docker container:
```
docker build . -t test
```

The purpose of the derived container is to ship the arangosh to run the tests in.

Running the docker container, parametrizing the connection endpoints of the cluster:
```
docker run test:latest --frontends tcp://192.168.173.88:9629 \
                       --frontends tcp://192.168.173.88:9729 \
                       --frontends tcp://192.168.173.88:9529 \
                       --scenario scenarios/cluster_replicated.yml
```

# nightly tar docker container
This container is intended to test the nightly tar packages whether starter deployment upgrades are working properly.

Build the container for later use with:
```
docker build docker_tar/ -t arangodb/release-test-automation
```

Run the container from within the office network; DNS lookup outside of the docker container:
```
docker run \
  -v `pwd`:/home/release-test-automation \
  -v /home/willi/Downloads/:/home/package_cache \
  -v /tmp/versions:/home/versions \
  --init \
  arangodb/release-test-automation \
   --old-version 3.7.7-nightly \
   --new-version 3.8.0-nightly \
   --remote-host $(host nas02.arangodb.biz |sed "s;.* ;;")
```

Run the container from abroad:
```
docker run  \
  -v `pwd`:/home/release-test-automation \
  -v /home/willi/Downloads/:/home/package_cache \
  -v /tmp/versions:/home/versions \
  --init \
  arangodb/release-test-automation \
    --old-version 3.7.7-nightly --new-version 3.8.0-nightly \
    --source http:stage2 --httpuser user --httppassvoid passvoid
```

## Wikipedia dump tests
These tests use the CSV data from the wikip
 http://home.apache.org/~mikemccand/enwiki-20120502-lines-1k.txt.lzma


# Allure reporting
To view allure report, you must have allure installed in your system. Download link(for Linux):
https://repo.maven.apache.org/maven2/io/qameta/allure/allure-commandline/2.17.2/allure-commandline-2.17.2.zip

After the test run is finished, run the following command:
```bash
allure serve [results_dir]
```
Default results dir: allure_results
This will open a browser with the test report.

# Maintaining code quality
## Formatter
We use [Black Formatter](https://github.com/psf/black). To apply formatting to the code simply run `black .` in the project root dir.  
Formatter settings are stored in `pyproject.toml` file.
To switch formatting off for a code block, start it with `# fmt: off` and end with `# fmt: on`.  
To disable formatting for single line, end it with `# fmt: on`. 

## Linter
We use [pylint](https://pylint.org/). Command to run it: `pylint release_tester`

### source "Installer"
In RTA an "installer" makes the ArangoDB version available in the system. By default, the native installer to the system is chosen.
With `--zip` the Windows Zip or Mac/Linux .tar.gz package is chosen. Similar to this `--src` flips the switch of not deploying a package
via an installer at all, but rather choose a source directory with compiled binaries to launch.
The source directory (directories in case of running upgrade) should contain `build/bin` with the compiled result binaries inside.

Several binaries are not built from with the arangodb source. They have to be added as copy or symlink to the bin directory.
They can easily be obtained through nightly zip/tar packages or be build from their respective source directories and symlinked into the `build/bin` directories:
- arangodb - the starter.
- arangosync - the arangosync binary for dc2dc replication
- rclone-arangodb 

The source directory is located via 3 parameters (and if `build/bin` exists chosen accordingly):
- `--package-dir` - in `test.py` this can be used to directly point to the source directory. Alternatively, subdirectories with symlinks can be used:
- `--new-version` if you specify `3.10.0-devel` (a semver valid version) (and --[no-]enterprise) this will result in this directory: `[package-dir]/[E_]3.10.0-devel`
- `--old-version` in `upgrade.py` this is used for the old version to upgrade from, works similar as `--new-version`.

If `--enterprise` is specfied, RTA treats this as an enterprise deployment, HotBackup and DC2DC becomes available.
Additionally the enterprise javascript files are added via cli parameters to arangosh and arangod / starter.

```
./release_tester/test.py --src \
  --enterprise \
  --package-dir ../devel \
  --new-version 3.10.0-devel \
  --starter-mode DC
```

or running an upgrade:
(To adjust this a bit strict directory naming conventions, symbolic links are used)

```
mkdir arangoversions
cd arangoversions
ln -s /home/willi/src/stable-3.9 E_3.9.0
ln -s /home/willi/src/devel E_3.10.0-devel
cd ..
./release_tester/upgrade.py --src \
  --enterprise \
  --package-dir $(pwd)/arangoversions \
  --new-version 3.10.0-devel \
  --old-version 3.9.0 \
  --starter-mode DC
```

Will search for `/home/willi/src/rta/arangoversions/E_3.9.0/build/bin` to launch the deployment initially, and upgrade to `/home/willi/src/rta/arangoversions/E_3.10.0-devel/build/bin`.

