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
  `apt-get install python3-yaml python3-magic python3-requests python3-click python3-distro python3-psutil python3-pexpect python3-pyftpdlib python3-statsd python3-selenium python3-pip gdb`

  the `python3-semver` on debian is to old - need to use the pip version instead:
  `pip3 install semver beautifultable allure_python_commons certifi tabulate`

  Ubuntu 16.40 pip3 system package is broken. Fix like this:
  `dpkg -r python3-pip python3-pexpect`
  `python3.8 -m easy_install pip`
  `pip install distro semver pexpect psutil beautifultable allure_python_commons certifi`

- **centos**:
   `yum update ; yum install python3 python3-pyyaml python3-magic python36-PyYAML python3-requests python3-click gcc platform-python-devel python3-distro python3-devel python36-distro python36-click python36-pexpect python3-pexpect python3-pyftpdlib; pip3 install psutil semver beautifultable` 
   `sudo yum install gdb`
- **plain pip**:
  `pip3 install psutil pyyaml pexpect requests click semver magic ftplib selenium beautifultable tabulate allure_python_commons certifi`
  or:
  `pip install -r requirements.txt`

## Mac OS
:
    `brew install libmagic`
    `brew install gnu-tar`
    `pip3 install click psutil requests pyyaml semver magic pexpect selenium beautifultable tabulate allure_python_commons certifi`
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

Alternatively selenoid may be used using:

    --selenium Remote_chrome
    --selenium-driver-args "command_executor=http://192.168.1.1:4444/wd/hub
    --publicip 192.168.1.1

 (where  `192.168.1.1` would be the real IP of your machine. Please note that you need to launch the selenoid server.)

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
 - `--[no-]check_locale` (true by default) whether the locale should be revalidated
 - `--test-data-dir` - the base directory where the tests starter instances should be created in (defaults to `/tmp/`)
 - `--mode [_all_|install|uninstall|tests]`
   - `all` (default) is intended to run the full flow. This is the production flow.
   - `install` to only install the package onto the system and store its setting to the temp folder (development) 
   - `tests`  to read the config file from the temp folder and run the tetss.
   - `uninstall` to clean up your system.
 - `--starter-mode [all|SG|LF|AFO|CL|DC|DCendurance|none]` which starter test to exute, `all` of them or `none` at all or:
   - `SG` - Single server - the most simple deployment possible
   - `LF` - Leader / Follower - setup two single instances, start replication between them
   - `AFO` - Active Failover - start the agency and servers for active failover, test failovers, leader changes etc.
   - `CL` - Cluster - start a cluster with 3 agents, 3 db-servers, 3 coordinators. Test stopping one. 
   - `DC` - setup 2 clusters, connect them with arangosync (enterprise only, non-Windows)
   - `DCendurance` - use DC setup to launch long running arangobenches (not part of `all`)
 - `--test` filter for tests of makedata / check data; comma separated list.
 - `--publicip` the IP of your system - used instead of `localhost` to compose the interacitve URLs.
 - `--verbose` if specified more logging is done
 - `--selenium` - specify the webdriver to be used to work with selenium (if)
 - `--selenium-driver-args` - arguments to the selenium browser - like `headless`
 - `--alluredir` - directory to save test results in allure format (default = allure-results)
 - `--clean-alluredir/--do-not-clean-alluredir` - clean allure directory before running tests (default = True)
 - `--[no-]ssl` use SSL (default = False)
 - `--[no-]replication2` use replication v.2 if applicable(version must be 3.12.0 or above) (default = False)
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
 - `--[no-]check_locale` (true by default) whether the locale should be revalidated
 - `--test-data-dir` - the base directory where the tests starter instances should be created in (defaults to `/tmp/`)
 - `--publicip` the IP of your system - used instead of `localhost` to compose the interacitve URLs.
 - `--verbose` if specified more logging is done
 - `--starter-mode [all|SG|LF|AFO|CL|DC|none]` which starter test to exute, `all` of them or `none` at all or:
   - `SG` - Single server - the most simple deployment possible
   - `LF` - Leader / Follower - setup two single instances, start replication between them
   - `AFO` - Active Failover - start the agency and servers for active failover, test failovers, leader changes etc.
   - `CL` - Cluster - start a cluster with 3 agents, 3 db-servers, 3 coordinators. Test stopping one. 
   - `DC` - setup 2 clusters, connect them with arangosync (enterprise only, non Windows and non Mac)
 - `--test` filter for tests of makedata / check data; comma separated list.
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
 - `--[no-]check_locale` (true by default) whether the locale should be revalidated
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
 - `--[no-]check_locale` (true by default) whether the locale should be revalidated
 - `--verbose` if specified more logging is done
 - `--alluredir` - directory to save test results in allure format (default = allure-results)
 - `--clean-alluredir/--do-not-clean-alluredir` - clean allure directory before running tests (default = True)

# Using `run_license_tests.py` to test the license manager feature

License manager tests are only applicable to enterprise edition.
Supported Parameters:
 - `--new-version` which Arangodb Version you want to run the test on
 - `--package-dir` The directory where you downloaded the nsis .exe / deb / rpm [/ dmg WIP]
 - `--[no-]interactive` (false if not invoked through a tty) whether at some point the execution should be paused for the user to execute manual tests with provided the SUT
 - `--[no-]check_locale` (true by default) whether the locale should be revalidated
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
 - `--force-arch` override the machine architecture of the host; [`aarch64`, ...] 
 - `--force-os ['', windows, mac, ubuntu, debian, centos, redhat, alpine]`, to download the software for another OS than the one you're currently running

example usage:
`python3 release_tester/download.py --enterprise \
                                    --new-version '3.7.1-rc.1+0.501' \
                                    --enterprise-magic <enterprisekey> \
                                    --package-dir /home/willi/Downloads/ \
                                    --force \
                                    --source ftp:stage2`

# using `down_upload.py` above `download.py` to upload files to a remote test target

`down_upload.py` uses `download.py` but will download enterprise and community, plus scp it to a remote host

Supported Parameters (above download.py)
- `--push-host` machine to SCP to.
- `--push-user` user to connect to remote host. defaults to `tester`
- `--ssh-key-file` ssh key to connect to machine

It is assumed that `ssh-agent` is utilized for authentification

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
 - `--[no-]check_locale` (true by default) whether the locale should be revalidated
 - `--test-data-dir` - the base directory where the tests starter instances should be created in (defaults to `/tmp/`)
 - `--publicip` the IP of your system - used instead of `localhost` to compose the interacitve URLs.
 - `--verbose` if specified more logging is done
 - `--starter-mode [all|SG|LF|AFO|CL|DC|none]` which starter test to exute, `all` of them or `none` at all or:
   - `SG` - Single server - the most simple deployment possible
   - `LF` - Leader / Follower - setup two single instances, start replication between them
   - `AFO` - Active Failover - start the agency and servers for active failover, test failovers, leader changes etc.
   - `CL` - Cluster - start a cluster with 3 agents, 3 db-servers, 3 coordinators. Test stopping one. 
   - `DC` - setup 2 clusters, connect them with arangosync (enterprise only, non-Windows and non-Mac)
 - `edition` which type to launch:
   - `C` community
   - `EP` enterprise
   - `EE` enterprise with encryption at rest
 - `--test` filter for tests of makedata / check data; comma separated list.
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
 - `--test/--no-test` specify whether to run clean installation tests on the new version(default = True)
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
 - `--starter-mode [all|SG|LF|AFO|CL|DC|none]` which starter test to exute, `all` of them or `none` at all or:
   - `SG` - Single server - the most simple deployment possible
   - `LF` - Leader / Follower - setup two single instances, start replication between them
   - `AFO` - Active Failover - start the agency and servers for active failover, test failovers, leader changes etc.
   - `CL` - Cluster - start a cluster with 3 agents, 3 db-servers, 3 coordinators. Test stopping one. 
   - `DC` - setup 2 clusters, connect them with arangosync (enterprise only, non-Windows, upgrade non Mac)
 - `edition` which type to launch:
   - `C` community
   - `EP` enterprise
   - `EE` enterprise with encryption at rest
 - `--test` filter for tests of makedata / check data; comma separated list.
 - `--selenium` - specify the webdriver to be used to work with selenium (if)
 - `--selenium-driver-args` - arguments to the selenium browser - like `headless`
 - `--alluredir` - directory to save test results in allure format (default = allure-results)
 - `--clean-alluredir/--do-not-clean-alluredir` - clean allure directory before running tests (default = True)
 - `--[no-]ssl` use SSL (default = False)
 - `--use-auto-certs` use self-signed SSL certificates (only applicable when using --ssl)
 - `--abort-on-error/--do-not-abort-on-error` - abort if one of the deployments failed
 - `--run-test-suites/--do-not-run-test-suites` - run test suites for each version pair (default = True)
Example usage: 

- [jenkins/nightly_tar.sh](jenkins/nightly_tar.sh) Download nightly tarball packages, and run it with selenium in `containers/docker_tar` ubuntu container
- [jenkins/nightly_deb.sh](jenkins/nightly_deb.sh) Download nightly debian packages, and run them with selenium in `containers/docker_deb` ubuntu container
- [jenkins/nightly_rpm.sh](jenkins/nightly_rpm.sh) Download nightly redhat packages, and run them with selenium in `containers/docker_rpm` centos 7 container


# Using `mixed_download_upgrade_test.py` for automated mixed source & zip testing

`mixed_download_upgrade_test.py` integrates `test.py`, `upgrade.py` and `download_packages.py`.
It intends to use a source built to upgrade from/to. Hence we cannot switch between community & enterprise. 
Thus it requires `--edition C` to be specified switch between Enterprise and community setups. 
It will download tar/zip packages, while `-nightly` will first attempt
to resolve the proper version of the nightly package, since `-nightly` allways is a suffix to the latest released version + 1.

The `BASE_DIR` environment variable is meant to be specified by oskar to find the oskar typical directory structure in there. 

It will then run the `upgrade.py` and `test.py` mechanic for either:
 - enterprise with encryption at rest enabled
 - enterprise
or:
 - community

and create a final report at the end of the run.

The downloading of packages can be circumvented by specifying `--source local`.

Supported Parameters:
 - `--new-version`
   - new: This is the to be released version. it will be downloaded from `--source`.
 - `--upgrade-matrix list` specify a list of upgrades to run. For all other versions, `--other-source` will
   be used to specify the download source. The list is specified in the format of: (without blanks)
     `first-From : first-To ; second-From : second-To`
 - `--test/--no-test` specify whether to run clean installation tests on the new version(default = False)
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
 - `--starter-mode [all|SG|LF|AFO|CL|DC|none]` which starter test to exute, `all` of them or `none` at all or:
   - `SG` - Single server - the most simple deployment possible
   - `LF` - Leader / Follower - setup two single instances, start replication between them
   - `AFO` - Active Failover - start the agency and servers for active failover, test failovers, leader changes etc.
   - `CL` - Cluster - start a cluster with 3 agents, 3 db-servers, 3 coordinators. Test stopping one. 
   - `DC` - setup 2 clusters, connect them with arangosync (enterprise only, non-Windows, upgrade non Mac)
 - `edition` which type to launch:
   - `C` community
   - `EP` enterprise
   - `EE` enterprise with encryption at rest
 - `--test` filter for tests of makedata / check data; comma separated list.
 - `--selenium` - specify the webdriver to be used to work with selenium (if)
 - `--selenium-driver-args` - arguments to the selenium browser - like `headless`
 - `--alluredir` - directory to save test results in allure format (default = allure-results)
 - `--clean-alluredir/--do-not-clean-alluredir` - clean allure directory before running tests (default = True)
 - `--[no-]ssl` use SSL (default = False)
 - `--use-auto-certs` use self-signed SSL certificates (only applicable when using --ssl)
 - `--abort-on-error/--do-not-abort-on-error` - abort if one of the deployments failed
 - `--run-test-suites/--do-not-run-test-suites` - run test suites for each version pair (default = False)

Example usage:
```
export BASE_DIR=/home/willi/src/develc/release-test-automation
./release_tester/mixed_download_upgrade_test.py --new-version 3.12.0 --upgrade-matrix '3.11.0-nightly:3.12.0-src' --starter-mode SG
```

# Using cleanup.py to clean out the system

`cleanup.py` will try to invoke all known cleanup mechanisms, to bring your system as much as possible into a 'pure' state.

 - `--zip` switches from system packages to the tar.gz/zip package for the cleanup.


# Using `deployment` scripts to install all the necessary dependency packages for testsystems
The scripts in the `deployment` directory will try to install all the required pacakges to a new/fresh machine in order to run release-test-automation tests.

# binaries strip cheking

 - Linux (ubuntu|debian|centos|fedora|sles)[deb|rpm|tar.gz] full support.
 - Mac [dmg|tar.gz] support through resource intense copy & compare; GO binaries such as `arangodb` and `arangosync` are assumed not to be stripped, since the mac strip command will fail for them.
 - Windows no supported yet.

# Source distribution

 - `release_tester/down_upload.py` - download packages via our various distribution routes, push to remote SUTs via scp
 - `release_tester/download.py` - download packages via our various distribution routes
 - `release_tester/[full_|mixed_|][download_][upgrade|&test].py` - main entrypoints to the process flow, download, install, run test, uninstall, cleanup
 - `release_tester/test_driver.py` dispatcher from the entrypoints in the different testparts, after download took place.
 - `release_tester/common_options.py` commandline options used by more than one entrypoint script
 - `release_tester/cleanup.py` - remove files and installed packages etc.
 - `release_tester/siteconfig.py` shared with Oskar, manages SUT capacity for timeouts etc. 
 - `release_tester/installers/[base|nsis|tar|linux|deb|rpm|mac].py`
   distribution / OS specific [un]installation/upgrade automation
   - `__init__.py` Configuration objects
     - Hot backup / rclone configurations
     - `InstallerConfig` contains system / installation components as versions etc.
     - `RunProperties` runner specific configurations
     - `EXECUTION_PLAN` pre-defined list of things to test during the full automatic release flow
     - `InstallerBaseConfig` simple config to bootstrap an installer
   - `binary_description.py` binary validation and description code, (windows specific parts)
   -  `base.py.py`
     - `InstallerBase`:
       - meta class for installers
       - shared code containing the list of binaries to be found
       - shared control code to revalidate binaries to be installed
       - code do decypher versions of binaries
     `InstallerArchive` shared base class for zip/tar/source installers

 - `release_tester/arangodb/agency.py`code to manipulate the agency
 - `release_tester/arangodb/instance.py`
   - manage arangosync & arangod instances.
   - detects their operation mode (Running, stopped, crashed, manually started/stopped)
   - Contains Blacklists to ignore while scanning logfiles for errors.
 - `release_tester/arangodb/async_client.py`
   manages subrocess execution; shared between rta/oskar/circle-ci
   provides the ability to portabily capture  log output
 - `release_tester/arangodb/sh.py` launch an arangosh with javascript snippets against the starter installation, rta-makedata, testing.js style
 - `release_tester/arangodb/sync.py` manage arangosync invocations
 - `release_tester/arangodb/backup.py` manage arangobackup invocations
 - `release_tester/arangodb/starter/manager.py` manage one starter instance and get information about its launched processes
 - `release_tester/arangodb/starter/deployments/[runner|leaderfolower|activefailover|cluster|cluster_perf|dc2dc|dc2dcendurance].py` set up one of [Leader/Follower | Active Failover | Cluster Cluster_Perf | DC2DC | DCendurance]
   - `__init__.py`
     - runner types / starter modes text vs. enum
     - basic runner spawning code
   - `runner.py`
     - `RunnerProperties` settings specific to the to be spawned runner, like SUT requirements
     - `Runner` base class for runners, application flow, lots of hooks, tool methods
 - `release_tester/arangodb/stress` tools to stress the SUT by launching multiple parallel configureable subjobs
   Orchestrated by `release_tester/arangodb/starter/deployments/cluster_perf.py` and `scenarios/`.
   - `restore.py` launch arangorestore jobs
   - `makedata.py` launch (multiple) rta-makedatas
   - `arangosh.py` launch (multiple) arangosh with various to be specified scripts
   - `dump.py` launch arangodump.
 - `release_tester/tools` several utility functions
 - `test_data` - UI related test data
 - `rta_makedata` - the famous makedata suite as reference
 - `attic_snippets` - trial and error scripts of start phase, utility functions like killall for mac/windows for manual invocation

 - `containers/` the source `Dockerfile`s of various docker containers
 - `jenkins/build_and_push_containers.sh` push one set of [amd64|arm64-v8] containers
 - `jenkins/build_and_push_manifests.sh` join above containers
 - `jenkins/nightly*.sh`, `jenkins/oscar_tar.sh` entrypoint scripts to be invoked from jenkins or manual
   - will evaluate `*VERSION*` environment variables as default
   - will pass `$@` into the rta invocation inside the docker contanier
   - will basically consist of invoking common snippets, only docker launches will be individual in here
 - `jenkins/common` - snippet parts used by the various entry point scripts; sourced by the "host"-script to have variable back/forwards passing, which isn't better possible in bash
    - common variables shared among these scripts:
       - `TRAP_COMMAND` array to push commands to that will be invoked by `trap` at the end of the script
       - `DOCKER_NETWORK_NAME` the network to be shared amongst the various containers
       - `DOCKER_ARGS`- the (common) arguments to the to be launched docker test-container
       - `RTA_ARGS` - array of arguments to be passed to the rta-invocation
    - `default_variables.sh` - common environment variable parsing setting
    - `default_matrix.sh` - common matrix environment variable parsing setting
    - `setup_docker.sh` - configure mountpoints etc. for the SUT-container, setup networks etc.
    - `set_max_map_count.sh` - make sure files and /proc are properly configured
    - `setup_selenium.sh` - launch the selenoid containers if `--selenium.*` in `$@`
    - `evaluate_force.sh` - whether force should be applied
    - `load_git_submodules.sh` - checkout submodules and enterprise closed parts (in able)
    - `launch_minio.sh` - launch the s3 lookalike minio container
    - `register_cleanup_trap.sh` - set the exit-trap for cleanup with all registered arguments
    /now tests will be executed/
    - `cleanup_ownership.sh` - de-root-ify all files
    - `gather_coredumps.sh` - check for crashes, zip files
    - `pre_cleanup_docker.sh` - make sure we can launch docker contaniers properly

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
 - run cluster_perf.py
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
 - `--[no-]check_locale` (true by default) whether the locale should be revalidated
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

## Pre-commit hooks
We have pre-commit hooks to enforce the use of linter and formatter.
The hooks are managed using the [pre-commit tool](https://pre-commit.com/). The configuration is stored in the `.pre-commit-config.yaml` file.  
To install pre-commit hooks:
- Run `pip install -r requirements.txt`
- Run `pre-commit install`

Now, each time you run `git commit`, the linter and formatter will be ran automatically. The hooks will prevent you from commiting code if the changed files have any unresolved issues found by the linter.  
  If the formatter changed anything in the files staged for commit, the hook will also not commit anything. You should review changes made by the formatter, stage them by running `git add` and run `git commit` again.

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
