#!/usr/bin/env python3
""" run an installer for the detected operating system """
import logging
import re
import os
import subprocess
from pathlib import Path
from abc import abstractmethod, ABC
import yaml
from arangodb.log import ArangodLogExaminer

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

STRIPPED_BINARIES = []
NON_STRIPPED_BINARIES = []
INSTALLED_SYMLINKS = []
ENTERPRISE_BINARIES = []

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


#pylint: disable=attribute-defined-outside-init
class InstallerBase(ABC):
    """ this is the prototype for the operation system agnostic installers """
    @abstractmethod
    def calculate_package_names(self):
        """ which filenames will we be able to handle"""

    @abstractmethod
    def install_package(self):
        """ install the packages to the system """

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

    def get_arangod_conf(self):
        """ where on the disk is the arangod config installed? """
        return self.cfg.cfgdir / 'arangod.conf'

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
        with open(self.calc_config_file_name()) as fileh:
            self.cfg = yaml.load(fileh, Loader=yaml.Loader)
        self.log_examiner = ArangodLogExaminer(self.cfg)

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
        global STRIPPED_BINARIES
        global NON_STRIPPED_BINARIES
        global INSTALLED_SYMLINKS
        global ENTERPRISE_BINARIES

        STRIPPED_BINARIES = [
            self.cfg.bin_dir / 'arangobackup',# enterprise
            self.cfg.bin_dir / 'arangoexport',
            self.cfg.bin_dir / 'arangoimport',
            self.cfg.bin_dir / 'arangorestore',
            self.cfg.bin_dir / 'arangobench',
            self.cfg.bin_dir / 'arangodump',
            self.cfg.bin_dir / 'arangosh',
            self.cfg.bin_dir / 'arangovpack',
            self.cfg.sbin_dir / 'arangod',
            self.cfg.sbin_dir / 'rclone-arangodb'] # enterprise

        NON_STRIPPED_BINARIES = [
            self.cfg.sbin_dir / 'arangosync', # enterprise
            self.cfg.bin_dir / 'arangodb']

        INSTALLED_SYMLINKS = [
            self.cfg.bin_dir / 'arangoimp',
            self.cfg.bin_dir / 'arangoinspect',
            self.cfg.bin_dir / 'arangosync', # enterprise
            self.cfg.bin_dir / '/arango-dfdb',
            self.cfg.sbin_dir / 'arango-init-database',
            self.cfg.sbin_dir / 'arango-secure-installation']

        ENTERPRISE_BINARIES = [
            self.cfg.bin_dir / 'arangobackup',# enterprise
            self.cfg.bin_dir / 'arangosync', # enterprise
            self.cfg.sbin_dir / 'rclone-arangodb'] # enterprise

    def check_is_stripped(self, file_to_check, expect_stripped):
        """ check whether this file is stripped (or not) """
        output = run_file_command(file_to_check)
        if expect_stripped and output.find(', stripped') < 0:
            raise Exception("expected " + file_to_check +
                            " to be stripped, but its not: " + output)
        if not expect_stripped and output.find(', not stripped') < 0:
            raise Exception("expected " + file_to_check +
                            " to be stripped, but its not: " + output)

    def check_symlink(self, file_to_check):
        """ check whether this file is a symlink """
        return file_to_check.is_symlink()

    def check_enterprise_file(self, file_to_check):
        """ checks whether a file exists in non/enterprise installations """
        exists = file_to_check.exists()
        try:
            ENTERPRISE_BINARIES.index(str(file_to_check))
            if self.cfg.enterprise and not exists:
                raise Exception("Binary missing from enterprise package!" +
                                str(file_to_check))
        except ValueError:
            if not self.cfg.enterprise and exists:
                raise Exception("Enterprise binary found in community package!"
                                + str(file_to_check))
        return exists

    def check_installed_files(self):
        """ check whether all files are installed and are non/stripped """
        for symlink in INSTALLED_SYMLINKS:
            if (self.check_enterprise_file(symlink)
                and not self.check_symlink(symlink)):
                raise Exception("should be a symlink: " +
                                str(symlink))

        for stripped_file in STRIPPED_BINARIES:
            if self.check_enterprise_file(stripped_file):
                self.check_is_stripped(stripped_file, True)

        for non_stripped_file in NON_STRIPPED_BINARIES:
            if self.check_enterprise_file(non_stripped_file):
                self.check_is_stripped(non_stripped_file, False)
        logging.info("files ok.")

    def check_uninstall_cleanup(self):
        """ check whether all is gone after the uninstallation """
        success = True

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
