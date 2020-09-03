#!/usr/bin/env python3
""" run an installer for the detected operating system """
import logging
import re
import os
import copy
import subprocess
import platform
from pathlib import Path
from abc import abstractmethod, ABC
import yaml
from arangodb.instance import ArangodInstance
from tools.asciiprint import ascii_print, print_progress as progress

## helper functions
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

is_windows = platform.win32_ver()[0]
extension = ''
if is_windows:
    extension = '.exe'
## helper classes
class BinaryDescription():
    """ describe the availability of an arangodb binary and its properties """
    def __init__(self, path, name, enter, strip, vmin, vmax, sym):
        global winver
        self.path = path / (name + extension)
        self.enterprise = enter
        self.stripped = strip
        self.version_min = vmin
        self.version_max = vmax
        self.symlink = sym

        for attribute in (
                self.path,
                self.enterprise,
                self.stripped,
                self.version_min,
                self.version_max,
                self.symlink
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
        """.format(self)


    def check_installed(self, version, enterprise, check_stripped, check_symlink):
        """ check all attributes of this file in reality """
        #TODO consider only certain verions
        #use semver package

        self.check_path(enterprise)

        if not enterprise and self.enterprise:
            #checks do not need to continue in this case
            return
        if check_stripped:
            self.check_stripped()
        if check_symlink:
            self.check_symlink()


    def check_path(self, enterprise):
        """ check whether the file rightfully exists or not """
        if enterprise and self.enterprise:
            if not self.path.is_file():
                raise Exception("Binary missing from enterprise package!" + str(self.path))

        #file must not exist
        if not enterprise and self.enterprise:
            if self.path.is_file():
                raise Exception("Enterprise binary found in community package!" + str(self.path))


    def check_stripped_mac(self):
        """ Checking stripped status of the arangod """
        # finding out the file size before stripped cmd invoked
        beforStripped = self.path.stat().st_size
        print('File size in bytes : ', beforStripped)

        to_file = Path('/tmp/test_whether_stripped')
        shutil.copy(str(self.path), str(to_file))
        
        # invoke the strip command on file_path
        cmd = ['strip', str(to_file)]
        # print(cmd)
        proc = subprocess.Popen(cmd, bufsize=-1,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE)

        print('stripped command invoked on' + str(to_file))
        # check the size of copied file after stripped
        afterStripped = to_file.stat().st_size
        print('File size in bytes : ', afterStripped)
        
        # checking both output size 
        if beforStripped == afterStripped:
            print('Stripped status: binary is stripped')
        else:
            print('Stripped status: binary is not stripped')
        
        
        if to_file.is_file():
            # invoke the delete command on file_path
            to_file.unlink(str(to_file))
            print(str(to_file) + 'file deleted after stripped check')
        else:
            print('stripped file not found')
        
    
    def check_stripped(self):
        """ check whether this file is stripped (or not) """
        output = run_file_command(self.path)
        if self.stripped and output.find(', stripped') < 0:
            raise Exception("expected " + str(self.path) +
                            " to be stripped, but its not: " + output)

        if not self.stripped and output.find(', not stripped') < 0:
            raise Exception("expected " + str(self.path) +
                            " to be stripped, but its not: " + output)
        
        # checking stripped state for macos
        macver = platform.mac_ver()
        if macver[0]:
            if self.check_stripped_mac() != self.stripped:
                 raise Exception("expected " + str(self.path) +
                            " to be stripped, but its not: " + output)
        else:
             print('Stripped checked successfully')


    def check_symlink(self):
        """ check whether the file exists and is a symlink (if) """
        for link in self.symlink:
            if not link.is_symlink():
                Exception("{0} is not a symlink".format(str(link)))


### main class
#pylint: disable=attribute-defined-outside-init
class InstallerBase(ABC):
    """ this is the prototype for the operation system agnostic installers """
    def __init__(self, cfg):
        self.arango_binaries = []
        self.cfg = copy.deepcopy(cfg)
        self.calculate_package_names()
        self.caclulate_file_locations()

        self.cfg.have_debug_package = False

    @abstractmethod
    def calculate_package_names(self):
        """ which filenames will we be able to handle"""

    @abstractmethod
    def install_package(self):
        """ install the packages to the system """

    @abstractmethod
    def upgrade_package(self):
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
        pass

    def install_debug_package(self):
        """ installing debug package """
        pass


    def get_arangod_conf(self):
        """ where on the disk is the arangod config installed? """
        return self.cfg.cfgdir / 'arangod.conf'

    def supports_hot_backup(self):
        """ by default hot backup is supported by the targets, there may be execptions."""
        return True

    def calc_config_file_name(self):
        """ store our config to disk - so we can be invoked partly """
        cfg_file = Path()
        if self.cfg.install_prefix == Path('/'):
            cfg_file = Path('/') / 'tmp' / 'config.yml'
        else:
            cfg_file = Path('c:') / 'tmp' / 'config.yml'
        return cfg_file

    def save_config(self):
        """ dump the config to disk """
        self.calc_config_file_name().write_text(yaml.dump(self.cfg))

    def load_config(self):
        """ deserialize the config from disk """
        verbose = self.cfg.verbose
        with open(self.calc_config_file_name()) as fileh:
            self.cfg = yaml.load(fileh, Loader=yaml.Loader)
        self.instance = ArangodInstance("single", self.cfg.port, self.cfg.localhost, self.cfg.publicip, self.cfg.logDir)
        self.calculate_package_names()
        self.cfg.verbose = verbose

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

    def enable_logging(self):
        """ if the packaging doesn't enable logging,
            do it using this function """
        arangodconf = self.get_arangod_conf().read_text()
        if not self.cfg.logDir.exists():
            self.cfg.logDir.mkdir(parents=True)
        new_arangod_conf = arangodconf.replace(
            '[log]',
            '[log]\nfile = ' +
            str(self.cfg.logDir / 'arangod.log'))
        print(new_arangod_conf)
        self.get_arangod_conf().write_text(new_arangod_conf)
        logging.info("arangod now configured for logging")

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

    def check_engine_file(self):
        """ check for the engine file to test whether the DB was created """
        if not Path(self.cfg.dbdir / 'ENGINE').is_file():
            raise Exception("database engine file not there!")


    def caclulate_file_locations(self):
        """ set the global location of files """

        self.arango_binaries = []

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_sbin_dir, 'arangod',
            False, True, "1.0.0", "4.0.0", [
                self.cfg.real_sbin_dir / 'arango-init-database',
                self.cfg.real_sbin_dir / 'arango-secure-installation'
            ]))

        # symlink only for MMFILES
        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_sbin_dir, 'arangod',
            False, True, "1.0.0", "3.6.0", [
                self.cfg.real_bin_dir / ('arango-dfdb' + extension)
            ]))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangosh',
            False, True, "1.0.0", "4.0.0", [
                self.cfg.real_bin_dir / ('arangoinspect' + extension)
            ]))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangoexport',
            False, True, "1.0.0", "4.0.0", []))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangoimport',
            False, True, "1.0.0", "4.0.0", [
                self.cfg.real_bin_dir / ('arangoimp' + extension)
            ]))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangodump',
            False, True, "1.0.0", "4.0.0", []))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangorestore',
            False, True, "1.0.0", "4.0.0", []))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangobench',
            False, True, "1.0.0", "4.0.0", []))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangovpack',
            False, True, "1.0.0", "4.0.0", []))

        #starter
        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangodb',
            False, False, "1.0.0", "4.0.0", []))

        ## enterprise
        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_bin_dir, 'arangobackup',
            True, True, "1.0.0", "4.0.0", []))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_sbin_dir, 'arangosync',
            True, False, "1.0.0", "4.0.0", [
                self.cfg.real_bin_dir / ('arangosync' + extension)
            ]))

        self.arango_binaries.append(BinaryDescription(
            self.cfg.real_sbin_dir, 'rclone-arangodb',
            True, True, "1.0.0", "4.0.0", []))

    def check_installed_files(self):
        """ check for the files whether they're installed """
        for binary in self.arango_binaries:
            progress("S" if binary.stripped else "s")
            binary.check_installed(self.cfg.version,
                                   self.cfg.enterprise,
                                   self.check_stripped,
                                   self.check_symlink)

        logging.info("all files ok")

    def check_uninstall_cleanup(self):
        """ check whether all is gone after the uninstallation """
        success = True

        if self.cfg.have_system_service:
            if (self.cfg.installPrefix != Path("/") and
                    self.cfg.installPrefix.is_dir()):
                logging.info("Path not removed: %s", str(self.cfg.installPrefix))
                success = False
            if os.path.exists(self.cfg.appdir):
                logging.info("Path not removed: %s", str(self.cfg.appdir))
                success = False
            if os.path.exists(self.cfg.dbdir):
                logging.info("Path not removed: %s", str(self.cfg.dbdir))
                success = False
        return success
