#!/usr/bin/env python3
""" run an installer for the detected operating system """
import logging
import re
import os
import copy
import subprocess
import platform
import shutil
import time
from pathlib import Path
from abc import abstractmethod, ABC
import semver
import yaml
import psutil
from arangodb.instance import ArangodInstance
from tools.asciiprint import print_progress as progress
from allure_commons._allure import attach
from reporting.reporting_utils import step


@step
def run_file_command(file_to_check):
    """ run `file file_to_check` and return the output """
    proc = subprocess.Popen(['file', file_to_check],
                            stdout=subprocess.PIPE,
                            stdin=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True)
    line = proc.stdout.readline()
    proc.wait()
    # print(line)
    return line

IS_WINDOWS = platform.win32_ver()[0]
FILE_EXTENSION = ''
if IS_WINDOWS:
    FILE_EXTENSION = '.exe'

IS_MAC = False
if platform.mac_ver()[0]:
    IS_MAC = True

## helper classes
class BinaryDescription():
    """ describe the availability of an arangodb binary and its properties """
    def __init__(self, path, name, enter, strip, vmin, vmax, sym, binary_type):
        # pylint: disable=R0913 disable=R0902
        self.path = path / (name + FILE_EXTENSION)
        self.enterprise = enter
        self.stripped = strip
        self.version_min = vmin
        self.version_max = vmax
        self.symlink = sym
        self.binary_type = binary_type

        for attribute in (
                self.path,
                self.enterprise,
                self.stripped,
                self.version_min,
                self.version_max,
                self.symlink,
                self.binary_type
        ):
            if attribute is None:
                logging.error("one of the given args is null")
                logging.error(str(self))
                raise ValueError

    def __repr__(self):
        return """
        path:        {0.path}
        enterprise:  {0.enterprise}
        stripped:    {0.stripped}
        version_min: {0.version_min}
        version_max: {0.version_max}
        symlink:     {0.symlink}
        binary_type: {0.binary_type}
        """.format(self)

    @step
    def check_installed(self,
                        version,
                        enterprise,
                        check_stripped,
                        check_symlink):
        """ check all attributes of this file in reality """
        if semver.compare(self.version_min, version) == 1:
            self.check_path(enterprise, False)
            return
        self.check_path(enterprise)

        if not enterprise and self.enterprise:
            #checks do not need to continue in this case
            return
        if check_stripped:
            self.check_stripped()
        if check_symlink:
            self.check_symlink()

    def check_path(self, enterprise, in_version = True):
        """ check whether the file rightfully exists or not """
        if enterprise and self.enterprise:
            if not self.path.is_file() and in_version:
                raise Exception("Binary missing from enterprise package!" +
                                str(self.path))
        #file must not exist
        if not enterprise and self.enterprise:
            if self.path.is_file():
                raise Exception(
                    "Enterprise binary found in community package!" +
                    str(self.path))

    def check_stripped_mac(self):
        """ Checking stripped status of the arangod """
        time.sleep(1)
        if self.binary_type == 'c++':
            # finding out the file size before stripped cmd invoked
            befor_stripped_size = self.path.stat().st_size

            to_file = Path('/tmp/test_whether_stripped')
            shutil.copy(str(self.path), str(to_file))
            # invoke the strip command on file_path
            cmd = ['strip', str(to_file)]
            proc = subprocess.Popen(cmd, bufsize=-1,
                                    stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE)
            proc.communicate()
            proc.wait()
            # check the size of copied file after stripped
            after_stripped_size = to_file.stat().st_size

            # cleanup temporary file:
            if to_file.is_file():
                to_file.unlink(str(to_file))
            else:
                print('stripped file not found')

            # checking both output size
            return befor_stripped_size == after_stripped_size
        # some go binaries are stripped, some not. We can't test it.
        return self.stripped

    def check_stripped_linux(self):
        """ check whether this file is stripped (or not) """
        output = run_file_command(self.path)
        if output.find(', stripped') >= 0:
            return True
        if output.find(', not stripped') >= 0:
            return False
        raise Exception("Strip checking: parse error for 'file " +
                        str(self.path) +
                        "', unparseable output:  [" +
                        output + "]")

    @step
    def check_stripped(self):
        """ check whether this file is stripped (or not) """
        is_stripped = True
        if IS_MAC:
            print('')
            # is_stripped = self.check_stripped_mac()
        else:
            is_stripped = self.check_stripped_linux()
            if not is_stripped and self.stripped:

                raise Exception("expected " + str(self.path) +
                            " to be stripped, but it is not stripped")

            if is_stripped and not self.stripped:
                raise Exception("expected " + str(self.path) +
                                " not to be stripped, but it is stripped")

    @step
    def check_symlink(self):
        """ check whether the file exists and is a symlink (if) """
        for link in self.symlink:
            if not link.is_symlink():
                Exception("{0} is not a symlink".format(str(link)))

    @step
    def un_install_package_for_upgrade(self):
        """ hook to uninstall old package for upgrade """

### main class
#pylint: disable=attribute-defined-outside-init disable=too-many-public-methods
class InstallerBase(ABC):
    """ this is the prototype for the operation system agnostic installers """
    def __init__(self, cfg):
        self.arango_binaries = []
        self.cfg = copy.deepcopy(cfg)
        self.calculate_package_names()
        self.caclulate_file_locations()

        self.cfg.have_debug_package = False
        self.reset_version(cfg.version)
        self.check_stripped = True
        self.check_symlink = True
        self.instance = None

    def reset_version(self, version):
        """ re-configure the version we work with """
        version = version.split("~")[0]
        version = ".".join(version.split(".")[:3])
        self.semver = semver.VersionInfo.parse(version)
        self.cfg.reset_version(version)

    @abstractmethod
    def calculate_package_names(self):
        """ which filenames will we be able to handle"""

    @abstractmethod
    def install_package(self):
        """ install the packages to the system """

    @abstractmethod
    def upgrade_package(self, old_installer):
        """ install a new version of the packages to the system """

    @abstractmethod
    def un_install_package(self):
        """ remove the installed packages from the system """

    @abstractmethod
    def check_service_up(self):
        """ check whether the system arangod service is running """

    @abstractmethod
    def start_service(self):
        """ launch the arangod system service """

    @abstractmethod
    def stop_service(self):
        """ stop the arangod system service """

    @abstractmethod
    def cleanup_system(self):
        """ if the packages are known to not properly cleanup - do it here. """

    def un_install_debug_package(self):
        """ Uninstalling debug package if it exist in the system """

    def install_debug_package(self):
        """ installing debug package """

    def un_install_package_for_upgrade(self):
        """ hook to uninstall old package for upgrade """

    def get_arangod_conf(self):
        """ where on the disk is the arangod config installed? """
        return self.cfg.cfgdir / 'arangod.conf'

    def supports_hot_backup(self):
        """ by default hot backup is supported by the targets,
        there may be execptions."""
        return semver.compare(self.cfg.version, "3.5.1") >=0

    def calc_config_file_name(self):
        """ store our config to disk - so we can be invoked partly """
        cfg_file = Path()
        if self.cfg.install_prefix == Path('/'):
            cfg_file = Path('/') / 'tmp' / 'config.yml'
        else:
            cfg_file = Path('c:') / 'tmp' / 'config.yml'
        return cfg_file

    @step
    def save_config(self):
        """ dump the config to disk """
        self.cfg.semver = None
        self.calc_config_file_name().write_text(yaml.dump(self.cfg))
        self.cfg.semver = semver.VersionInfo.parse(self.cfg.version)

    @step
    def load_config(self):
        """ deserialize the config from disk """
        verbose = self.cfg.verbose
        with open(self.calc_config_file_name()) as fileh:
            self.cfg = yaml.load(fileh, Loader=yaml.Loader)
        self.cfg.semver = semver.VersionInfo.parse(self.cfg.version)
        self.instance = ArangodInstance("single",
                                        self.cfg.port,
                                        self.cfg.localhost,
                                        self.cfg.publicip,
                                        self.cfg.log_dir,
                                        self.cfg.passvoid,
                                        True)
        self.calculate_package_names()
        self.cfg.verbose = verbose

    @step
    def broadcast_bind(self):
        """
        modify the arangod.conf so the system will broadcast bind
        so you can access the SUT from the outside
        with your local browser
        """
        arangodconf = self.get_arangod_conf().read_text()
        iprx = re.compile('127\\.0\\.0\\.1')
        new_arangod_conf = iprx.subn('0.0.0.0', arangodconf)
        self.get_arangod_conf().write_text(new_arangod_conf[0])
        logging.info("arangod now configured for broadcast bind")
        self.cfg.add_frontend('http', self.cfg.publicip, '8529')

    @step
    def enable_logging(self):
        """ if the packaging doesn't enable logging,
            do it using this function """
        arangodconf = self.get_arangod_conf().read_text()
        if not self.cfg.log_dir.exists():
            self.cfg.log_dir.mkdir(parents=True)
        new_arangod_conf = arangodconf.replace(
            '[log]',
            '[log]\nfile = ' +
            str(self.cfg.log_dir / 'arangod.log'))
        print(new_arangod_conf)
        attach(new_arangod_conf, "New arangod.conf")
        self.get_arangod_conf().write_text(new_arangod_conf)
        logging.info("arangod now configured for logging")

    @step
    def check_installed_paths(self):
        """ check whether the requested directories and files were created """
        if (
                not self.cfg.dbdir.is_dir() or
                not self.cfg.appdir.is_dir() or
                not self.cfg.cfgdir.is_dir()
        ):
            raise Exception("expected installation paths are not there")

        if not self.get_arangod_conf().is_file():
            raise Exception("configuration files aren't there")

    @step
    def check_engine_file(self):
        """ check for the engine file to test whether the DB was created """
        if not Path(self.cfg.dbdir / 'ENGINE').is_file():
            raise Exception("database engine file not there!")

    def output_arangod_version(self):
        """ document the output of arangod --version """
        psutil.Popen([self.cfg.sbin_dir / "arangod", '--version']).wait()

    @step
    def caclulate_file_locations(self):
        """ set the global location of files """
        self.arango_binaries = []
        stripped_arangod = semver.compare(self.cfg.version, "3.7.999") < 0
        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_sbin_dir, 'arangod',
            False,
            stripped_arangod,
            "1.0.0", "4.0.0", [
                self.cfg.real_sbin_dir / 'arango-init-database',
                self.cfg.real_sbin_dir / 'arango-secure-installation'
            ], 'c++'))

        # symlink only for MMFILES
        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_sbin_dir, 'arangod',
            False, stripped_arangod, "1.0.0", "3.6.0", [
                self.cfg.real_bin_dir / ('arango-dfdb' + FILE_EXTENSION)
            ], 'c++'))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangosh',
            False, True, "1.0.0", "4.0.0", [
                self.cfg.real_bin_dir / ('arangoinspect' + FILE_EXTENSION)
            ], 'c++'))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangoexport',
            False, True, "1.0.0", "4.0.0", [], 'c++'))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangoimport',
            False, True, "1.0.0", "4.0.0", [
                self.cfg.real_bin_dir / ('arangoimp' + FILE_EXTENSION)
            ], 'c++'))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangodump',
            False, True, "1.0.0", "4.0.0", [], 'c++'))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangorestore',
            False, True, "1.0.0", "4.0.0", [], 'c++'))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangobench',
            False, True, "1.0.0", "4.0.0", [], 'c++'))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangovpack',
            False, True, "1.0.0", "4.0.0", [], 'c++'))

        #starter
        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangodb',
            False, False, "1.0.0", "4.0.0", [], 'go'))

        # enterprise
        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangobackup',
            True, True, "3.5.1", "4.0.0", [], 'c++'))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_sbin_dir, 'arangosync',
            True, False, "1.0.0", "4.0.0", [
                self.cfg.real_bin_dir / ('arangosync' + FILE_EXTENSION)
            ], 'go'))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_sbin_dir, 'rclone-arangodb',
            True, True, "3.5.1", "4.0.0", [], 'go'))

    @step
    def check_installed_files(self):
        """ check for the files whether they're installed """
        if IS_MAC:
            print('Strip checking is disabled on DMG packages.')
        else:
            for binary in self.arango_binaries:
                progress("S" if binary.stripped else "s")
                binary.check_installed(self.cfg.version,
                                    self.cfg.enterprise,
                                    self.check_stripped,
                                    self.check_symlink)
        print('\n')
        logging.info("all files ok")

    @step
    def check_uninstall_cleanup(self):
        """ check whether all is gone after the uninstallation """
        success = True

        if self.cfg.have_system_service:
            if (self.cfg.installPrefix != Path("/") and
                    self.cfg.installPrefix.is_dir()):
                logging.info("Path not removed: %s",
                             str(self.cfg.installPrefix))
                success = False
            if os.path.exists(self.cfg.appdir):
                logging.info("Path not removed: %s", str(self.cfg.appdir))
                success = False
            if os.path.exists(self.cfg.dbdir):
                logging.info("Path not removed: %s", str(self.cfg.dbdir))
                success = False
        return success

    def set_system_instance(self):
        """
         set an instance representing the system service launched by packages
        """
        self.instance = ArangodInstance("single",
                                        "8529",
                                        self.cfg.localhost,
                                        self.cfg.publicip,
                                        (self.cfg.installPrefix /
                                         self.cfg.log_dir),
                                        self.cfg.passvoid,
                                        True)
