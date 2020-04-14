#!/usr/bin/env python3
""" run an installer for the detected operating system """
import logging
import re
import os
from pathlib import Path
from abc import abstractmethod, ABC
import yaml
from arangodb.log import ArangodLogExaminer

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


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
        self.get_arangod_conf().write_text(new_arangod_conf[0])
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
