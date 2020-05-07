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
from pprint import pprint as PP

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

ARANGO_BINARIES = []

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


## helper classes
class BinaryDescription():
    def __init__(self,path,enter,strip,vmin,vmax,sym):
        self.path = path
        self.enterprise = enter
        self.stripped = strip
        self.version_min = vmin
        self.version_max = vmax
        self.symlink = sym

        for x in (
            self.path,
            self.enterprise,
            self.stripped,
            self.version_min,
            self.version_max,
            self.symlink
        ):
            if x == None:
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


    def check_removed():
        #ensure file and symlinks do not exist
        pass

    def check_installed(self,version, enterprise):
        #TODO consider only certain verions
        #use semver package

        self.check_path(enterprise)

        if not enterprise and self.enterprise:
            #checks do not need to continue in this case
            return

        self.check_stripped()
        self.check_symlink()


    def check_path(self, enterprise):
        if enterprise and self.enterprise:
            if not self.path.is_file():
                raise Exception("Binary missing from enterprise package!" + str(self.path))

        #file must not exist
        if not enterprise and self.enterprise:
            if self.path.is_file():
                raise Exception("Enterprise binary found in community package!" + str(self.path))


    def check_stripped(self):
        """ check whether this file is stripped (or not) """
        output = run_file_command(self.path)
        if self.stripped and output.find(', stripped') < 0:
            raise Exception("expected " + str(self.path) + " to be stripped, but its not: " + output)

        if not self.stripped and output.find(', not stripped') < 0:
            raise Exception("expected " + str(self.path) + " to be stripped, but its not: " + output)

    def check_symlink(self):
        for link in self.symlink:
            """ check whether this file is a symlink """
            if not file_to_check.is_symlink():
                Exception("{0} is not a symlink".format(str(link)))


### main class
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
        verbose = self.cfg.verbose
        with open(self.calc_config_file_name()) as fileh:
            self.cfg = yaml.load(fileh, Loader=yaml.Loader)
        self.log_examiner = ArangodLogExaminer(self.cfg)
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
        global ARANGO_BINARIES

        ARANGO_BINARIES = []

        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.sbin_dir / 'arangod',
            False, True, "1.0.0", "4.0.0", [self.cfg.sbin_dir / 'arango-init-database', self.cfg.sbin_dir / 'arango-secure-installation'] )
        )

        # symlink only for MMFILES
        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.sbin_dir / 'arangod',
            False, True, "1.0.0", "3.6.0", [self.cfg.bin_dir / 'arango-dfdb' ] )
        )

        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.bin_dir / 'arangosh',
            False, True, "1.0.0", "4.0.0", [self.cfg.bin_dir / 'arangoinspect'] )
        )

        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.bin_dir / 'arangoexport',
            False, True, "1.0.0", "4.0.0", [] )
        )

        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.bin_dir / 'arangoimport',
            False, True, "1.0.0", "4.0.0", [self.cfg.bin_dir / 'arangoimp'] )
        )

        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.bin_dir / 'arangodump',
            False, True, "1.0.0", "4.0.0", [] )
        )

        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.bin_dir / 'arangorestore',
            False, True, "1.0.0", "4.0.0", [] )
        )

        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.bin_dir / 'arangobench',
            False, True, "1.0.0", "4.0.0", [] )
        )

        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.bin_dir / 'arangovpack',
            False, True, "1.0.0", "4.0.0", [] )
        )

        #starter
        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.bin_dir / 'arangodb',
            False, False, "1.0.0", "4.0.0", [] )
        )

        ## enterprise
        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.bin_dir / 'arangobackup',
            True, True, "1.0.0", "4.0.0", [] )
        )

        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.sbin_dir / 'arangosync',
            True, False, "1.0.0", "4.0.0", [self.cfg.bin_dir / 'arangosync'] )
        )

        ARANGO_BINARIES.append(BinaryDescription(
            self.cfg.sbin_dir / 'rclone-arangodb',
            True, True, "1.0.0", "4.0.0", [] )
        )


        for bin in ARANGO_BINARIES:
            bin.check_installed(self.cfg.version, self.cfg.enterprise)

        logging.info("all files ok")

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
