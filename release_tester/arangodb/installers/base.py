#!/usr/bin/env python3
""" run an installer for the detected operating system """
from abc import abstractmethod, ABC, ABCMeta
import copy
import logging
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import time

import magic
import semver
import yaml
import psutil

from arangodb.async_client import ArangoCLIprogressiveTimeoutExecutor, make_default_params
from arangodb.installers.binary_description import BinaryDescription, FILE_EXTENSION, FILE_PIDS
from arangodb.installers import InstallerConfig
from arangodb.instance import ArangodInstance
from tools.asciiprint import print_progress as progress
from allure_commons._allure import attach
from reporting.reporting_utils import step

IS_WINDOWS = platform.win32_ver()[0]

### main class
# pylint: disable=attribute-defined-outside-init disable=too-many-public-methods disable=too-many-instance-attributes
class InstallerBase(ABC):
    """this is the prototype for the operation system agnostic installers"""

    hot_backup: bool
    basedir: Path
    installer_type: str

    def __init__(self, cfg: InstallerConfig):
        self.arangods = cfg.arangods
        self.machine = platform.machine()
        self.arango_binaries = []
        self.backup_arangod_name = None
        self.cfg = copy.deepcopy(cfg)
        self.calculate_package_names()

        self.cfg.debug_package_is_installed = False
        self.cfg.client_package_is_installed = False
        self.cfg.server_package_is_installed = False
        self.reset_version(cfg.version)
        self.check_stripped = True
        self.check_symlink = True
        self.check_notarized = False
        self.server_package = ""
        self.debug_package = ""
        self.client_package = ""
        self.instance = None
        self.starter_versions = {}
        self.syncer_versions = {}
        self.rclone_versions = {}
        self.cli_executor = ArangoCLIprogressiveTimeoutExecutor(self.cfg, self.instance)
        self.core_glob = "**/*core"
        self.copy_for_result = True

    def reset_version(self, version):
        """re-configure the version we work with"""
        if version.find("nightly") >= 0:
            version = version.split("~")[0]
            version = ".".join(version.split(".")[:3])
        self.semver = semver.VersionInfo.parse(version)
        self.cfg.reset_version(version)

    @step
    def install_server_package(self):
        """install the server package to the system"""
        self.install_server_package_impl()
        self.cfg.server_package_is_installed = True
        self.calculate_file_locations()

    @step
    def copy_binaries(self):
        """store arangod binary for probable later analysis"""
        eps = "E_" if self.cfg.enterprise else ""
        self.backup_arangod_name = self.cfg.base_test_dir / f"arangod_{eps}_{self.cfg.version}{FILE_EXTENSION}"
        arangod_src = self.cfg.real_sbin_dir / f"arangod{FILE_EXTENSION}"
        if not str(self.backup_arangod_name) in self.arangods and arangod_src.exists():
            self.arangods.append(self.backup_arangod_name)
            print("copying " + str(arangod_src) + " to " + str(self.backup_arangod_name))
            shutil.copy(str(arangod_src), str(self.backup_arangod_name))

    @step
    def get_arangod_binary(self, target_dir):
        """adding arangod binary to report tarball"""
        if self.backup_arangod_name is None:
            self.copy_binaries()
        if self.backup_arangod_name.exists():
            print(f"copying {self.backup_arangod_name} => {target_dir}")
            shutil.copy(str(self.backup_arangod_name), target_dir)
        else:
            print(f"{str(self.backup_arangod_name)} is not there")

    @step
    def un_install_server_package(self):
        """uninstall the server package"""
        if self.cfg.debug_package_is_installed:
            self.un_install_debug_package()
        self.un_install_server_package_impl()
        self.cfg.server_package_is_installed = False

    @step
    def install_client_package(self):
        """install the client package to the system"""
        self.install_client_package_impl()
        self.cfg.client_package_is_installed = True
        self.calculate_file_locations()

    @step
    def un_install_client_package(self):
        """Uninstall client package"""
        self.un_install_client_package_impl()
        self.cfg.client_package_is_installed = False

    @step
    def install_debug_package(self):
        """install the debug package to the system"""
        ret = self.install_debug_package_impl()
        self.cfg.debug_package_is_installed = ret
        return ret

    @step
    def un_install_debug_package(self):
        """Uninstall debug package"""
        ret = self.un_install_debug_package_impl()
        self.cfg.debug_package_is_installed = ret
        return ret

    @step
    def un_install_server_package_for_upgrade(self):
        """if we need to do something to the old installation on upgrade, do it here."""

    def install_debug_package_impl(self):
        """install the debug package"""
        return False

    def un_install_debug_package_impl(self):
        """uninstall the debug package"""
        return False

    def __repr__(self):
        return (
            "Installer type: {0.installer_type}\n"
            + "Server package: {0.server_package}\n"
            + "Debug package: {0.debug_package}\n"
            + "Client package: {0.client_package}"
        ).format(self)

    @abstractmethod
    def calculate_package_names(self):
        """which filenames will we be able to handle"""

    @abstractmethod
    def install_server_package_impl(self):
        """install the packages to the system"""

    @abstractmethod
    def upgrade_server_package(self, old_installer):
        """install a new version of the server package to the system"""

    @step
    def upgrade_client_package(self, old_installer):
        """install a new version of the client package to the system"""
        self.upgrade_client_package_impl()
        self.cfg.client_package_is_installed = True
        self.calculate_file_locations()
        old_installer.cfg.client_package_is_installed = False

    def uninstall_everything(self):
        """uninstall all arango packages present in the system(including those installed outside this installer)"""
        self.uninstall_everything_impl()
        self.cfg.server_package_is_installed = False
        self.cfg.debug_package_is_installed = False
        self.cfg.client_package_is_installed = False

    def uninstall_everything_impl(self):
        """uninstall all arango packages present in the system(including those installed outside this installer)"""
        raise NotImplementedError("uninstall_everything_impl method is not implemented for this installer type")

    def upgrade_client_package_impl(self):
        """install a new version of the client package to the system"""
        self.install_client_package()

    @abstractmethod
    def check_service_up(self):
        """check whether the system arangod service is running"""

    @abstractmethod
    def start_service(self):
        """launch the arangod system service"""

    @abstractmethod
    def stop_service(self):
        """stop the arangod system service"""

    @abstractmethod
    def un_install_server_package_impl(self):
        """installer specific server uninstall function"""

    @abstractmethod
    def install_client_package_impl(self):
        """installer specific client uninstall function"""

    @abstractmethod
    def un_install_client_package_impl(self):
        """installer specific client uninstall function"""

    @abstractmethod
    def cleanup_system(self):
        """if the packages are known to not properly cleanup - do it here."""

    def get_arangod_conf(self):
        """where on the disk is the arangod config installed?"""
        return self.cfg.cfgdir / "arangod.conf"

    def supports_hot_backup(self):
        """by default hot backup is supported by the targets,
        there may be execptions."""
        return semver.compare(self.cfg.version, "3.5.1") >= 0

    @staticmethod
    def calc_config_file_name():
        """store our config to disk - so we can be invoked partly"""
        cfg_file = Path()
        if IS_WINDOWS:
            if "WORKSPACE_TMP" in os.environ:
                wdtmp = Path(os.environ["WORKSPACE_TMP"])
                wdtmp.mkdir(parents=True, exist_ok=True)
                cfg_file = wdtmp / "config.yml"
            else:
                cfg_file = Path("c:/") / "tmp/" / "config.yml"
        else:
            cfg_file = Path("/") / "tmp" / "config.yml"
        return cfg_file

    @step
    def save_config(self):
        """dump the config to disk"""
        self.cfg.semver = None
        cfg_file = self.calc_config_file_name()
        if cfg_file.exists():
            try:
                cfg_file.unlink()
            except PermissionError:
                self.cfg.semver = semver.VersionInfo.parse(self.cfg.version)
                print("Ignoring non deleteable " + str(cfg_file))
                return
        cfg_file.write_text(yaml.dump(self.cfg), encoding="utf8")
        self.cfg.semver = semver.VersionInfo.parse(self.cfg.version)

    @staticmethod
    def load_config_from_file(filename=None):
        """find config file on disk"""
        if not filename:
            filename = InstallerBase.calc_config_file_name()
        with open(filename, encoding="utf8") as fileh:
            print("loading " + str(filename))
            cfg = yaml.load(fileh, Loader=yaml.Loader)
            return cfg

    @step
    def load_config(self):
        """deserialize the config from disk"""
        # pylint: disable=broad-except
        verbose = self.cfg.verbose
        try:
            ext_cfg = InstallerBase.load_config_from_file()
            test_cfg = copy.deepcopy(self.cfg)
            test_cfg.set_from(ext_cfg)
            self.cfg.set_from(test_cfg)
        except Exception as ex:
            print("failed to load saved config - skiping " + str(ex))
            return
        self.cfg.semver = semver.VersionInfo.parse(self.cfg.version)
        self.instance = ArangodInstance(
            "single",
            self.cfg.port,
            self.cfg.localhost,
            self.cfg.publicip,
            self.cfg.log_dir,
            self.cfg.passvoid,
            True,
            self.cfg.version,
            self.cfg.enterprise,
        )
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
        iprx = re.compile("127\\.0\\.0\\.1")
        new_arangod_conf = iprx.subn("0.0.0.0", arangodconf)
        self.get_arangod_conf().write_text(new_arangod_conf[0])
        logging.info("arangod now configured for broadcast bind")
        self.cfg.add_frontend("http", self.cfg.publicip, "8529")

    @step
    def enable_logging(self):
        """if the packaging doesn't enable logging,
        do it using this function"""
        arangodconf = self.get_arangod_conf().read_text()
        if not self.cfg.log_dir.exists():
            self.cfg.log_dir.mkdir(parents=True)
        new_arangod_conf = arangodconf.replace("[log]", "[log]\nfile = " + str(self.cfg.log_dir / "arangod.log"))
        print(new_arangod_conf)
        attach(new_arangod_conf, "New arangod.conf")
        self.get_arangod_conf().write_text(new_arangod_conf)
        logging.info("arangod now configured for logging")

    @step
    def check_installed_paths(self):
        """check whether the requested directories and files were created"""
        if not self.cfg.dbdir.is_dir() or not self.cfg.appdir.is_dir() or not self.cfg.cfgdir.is_dir():
            raise Exception("expected installation paths are not there")

        if not self.get_arangod_conf().is_file():
            raise Exception("configuration files aren't there")

    @step
    def check_engine_file(self):
        """check for the engine file to test whether the DB was created"""
        if not Path(self.cfg.dbdir / "ENGINE").is_file():
            raise Exception("database engine file not there!")

    @step
    def output_arangod_version(self):
        """document the output of arangod --version"""
        return self.cli_executor.run_monitored(
            executeable=self.cfg.real_sbin_dir / "arangod",
            args=["--version"],
            params=make_default_params(True, "arangod versioncheck"),
            deadline=10,
        )

    @step
    def calculate_file_locations(self):
        """set the global location of files"""
        # files present in both server and client packages
        self.calculate_package_names()
        self.arango_binaries = []
        if self.cfg.client_package_is_installed or self.cfg.server_package_is_installed:
            self.arango_binaries.append(
                BinaryDescription(
                    self.cfg.real_bin_dir,
                    "arangosh",
                    "arangosh - commandline client",
                    False,
                    True,
                    "1.0.0",
                    "4.0.0",
                    [self.cfg.real_bin_dir / ("arangoinspect" + FILE_EXTENSION)],
                    "c++",
                )
            )

            self.arango_binaries.append(
               BinaryDescription(
                   self.cfg.real_bin_dir,
                   "arangoexport",
                   "arangoexport - data exporter",
                   False,
                   True,
                   "1.0.0",
                   "4.0.0",
                   [],
                   "c++",
               )
            )

            self.arango_binaries.append(
                BinaryDescription(
                    self.cfg.real_bin_dir,
                    "arangoimport",
                    "arangoimport - data importer",
                    False,
                    True,
                    "1.0.0",
                    "4.0.0",
                    [self.cfg.real_bin_dir / ("arangoimp" + FILE_EXTENSION)],
                    "c++",
                )
            )

            self.arango_binaries.append(
               BinaryDescription(
                   self.cfg.real_bin_dir,
                   "arangodump",
                   "arangodump - data and configuration dumping tool",
                   False,
                   True,
                   "1.0.0",
                   "4.0.0",
                   [],
                   "c++",
               )
           )

            self.arango_binaries.append(
               BinaryDescription(
                   self.cfg.real_bin_dir,
                   "arangorestore",
                   "arangrestore - data and configuration restoration tool",
                   False,
                   True,
                   "1.0.0",
                   "4.0.0",
                   [],
                   "c++",
               )
           )

            self.arango_binaries.append(
                BinaryDescription(
                    self.cfg.real_bin_dir,
                    "arangobench",
                    "arangobench.*",  #  - stress test tool",
                    False,
                    True,
                    "1.0.0",
                    "4.0.0",
                    [],
                    "c++",
                )
            )

            self.arango_binaries.append(
                BinaryDescription(
                    self.cfg.real_bin_dir,
                    "arangovpack",
                    "arangovpack - VelocyPack formatter",
                    False,
                    True,
                    "1.0.0",
                    "4.0.0",
                    [],
                    "c++",
                )
            )

            # enterprise
            self.arango_binaries.append(
                BinaryDescription(
                    self.cfg.real_bin_dir,
                    "arangobackup",
                    "arangobackup - hot backup tool",
                    True,
                    True,
                    "3.5.1",
                    "4.0.0",
                    [],
                    "c++",
                )
            )

        # files only present in server package
        if self.cfg.server_package_is_installed:
            self.arango_binaries.append(
                BinaryDescription(
                    self.cfg.real_sbin_dir,
                    "arangod",
                    "ArangoDB - the native multi-model NoSQL database",
                    False,
                    False,
                    "1.0.0",
                    "4.0.0",
                    [
                        self.cfg.real_sbin_dir / "arango-init-database",
                        self.cfg.real_sbin_dir / "arango-secure-installation",
                    ],
                    "c++",
                )
            )

            # symlink only for MMFILES
            self.arango_binaries.append(
                BinaryDescription(
                    self.cfg.real_sbin_dir,
                    "arangod",
                    "ArangoDB - the native multi-model NoSQL database",
                    False,
                    True,
                    "1.0.0",
                    "3.6.0",
                    [self.cfg.real_bin_dir / ("arango-dfdb" + FILE_EXTENSION)],
                    "c++",
                )
            )

            # starter
            self.arango_binaries.append(
                BinaryDescription(
                    self.cfg.real_bin_dir,
                    "arangodb",
                    "",
                    False,
                    False,
                    "1.0.0",
                    "4.0.0",
                    [],
                    "go",
                )
            )

            # enterprise
            self.arango_binaries.append(
                BinaryDescription(
                    self.cfg.real_sbin_dir,
                    "arangosync",
                    "",
                    True,
                    False,
                    "1.0.0",
                    "3.11.99",
                    [self.cfg.real_bin_dir / ("arangosync" + FILE_EXTENSION)],
                    "go",
                )
            )

            self.arango_binaries.append(
                BinaryDescription(
                    self.cfg.real_sbin_dir,
                    "rclone-arangodb",
                    "",
                    True,
                    True,
                    "3.5.1",
                    "4.0.0",
                    [],
                    "go",
                )
            )

    @step
    def check_installed_files(self):
        """check for the files whether they're installed"""
        # pylint: disable=global-statement
        global FILE_PIDS
        for binary in self.arango_binaries:
            progress("S" if binary.stripped else "s")
            binary.check_installed(
                self.semver, self.cfg.enterprise, self.check_stripped, self.check_symlink, self.check_notarized, False
            )
        print("\nran file commands with PID:" + str(FILE_PIDS) + "\n")
        FILE_PIDS = []
        logging.info("all files ok")

    @step
    def check_uninstall_cleanup(self):
        """check whether all is gone after the uninstallation"""
        success = True

        if self.cfg.have_system_service:
            if self.cfg.install_prefix != Path("/") and self.cfg.install_prefix.is_dir():
                logging.info("Path not removed: %s", str(self.cfg.install_prefix))
                success = False
            if os.path.exists(self.cfg.appdir):
                logging.info("Path not removed: %s", str(self.cfg.appdir))
                success = False
            if os.path.exists(self.cfg.dbdir):
                logging.info("Path not removed: %s", str(self.cfg.dbdir))
                success = False
        return success

    def get_log_dir(self):
        """get the directory the installer will create logs in"""
        return self.cfg.install_prefix / self.cfg.log_dir

    def set_system_instance(self):
        """
        set an instance representing the system service launched by packages
        """
        self.instance = ArangodInstance(
            typ="single",
            port="8529",
            localhost=self.cfg.localhost,
            publicip=self.cfg.publicip,
            basedir=(self.get_log_dir()),
            passvoid=self.cfg.passvoid,
            ssl=False,
            version=self.cfg.version,
            enterprise=self.cfg.enterprise,
        )

    def get_starter_version(self):
        """find out the version of the starter in this package"""
        if not self.starter_versions:
            starter = self.cfg.bin_dir / ("arangodb" + FILE_EXTENSION)
            if not starter.is_file():
                print("starter not found where we searched it? " + str(starter))
                return semver.VersionInfo.parse("0.0.0")
            # print(starter.stat())
            # print(starter.owner())
            # print(starter.group())
            # run_file_command(str(starter))
            starter_version_proc = psutil.Popen(
                [str(starter), "--version"],
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                universal_newlines=True,
            )
            line = starter_version_proc.stdout.readline()
            starter_version_proc.wait()
            string_array = line.split(", ")
            for one_str in string_array:
                splitted = one_str.split(" ")
                self.starter_versions[splitted[0]] = splitted[1]
                print("Starter version: " + str(self.starter_versions))
        return semver.VersionInfo.parse(self.starter_versions["Version"])

    def get_rclone_version(self):
        """find out the version of the starter in this package"""
        if not self.cfg.enterprise:
            return semver.VersionInfo.parse("0.0.0")
        if not self.rclone_versions:
            rclone = self.cfg.real_sbin_dir / ("rclone-arangodb" + FILE_EXTENSION)
            if not rclone.is_file():
                print("rclone not found where we searched it? " + str(rclone))
                return semver.VersionInfo.parse("0.0.0")
            print(rclone.stat())
            # print(rclone.owner())
            # print(rclone.group())
            print(magic.from_file(str(rclone)))
            rclone_version_proc = psutil.Popen(
                [str(rclone), "--version"],
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                universal_newlines=True,
            )
            line = rclone_version_proc.stdout.readline()
            rclone_version_proc.wait()
            print(line)
            string_array = line.split(", ")
            for one_str in string_array:
                splitted = one_str.split(" ")
                self.rclone_versions[splitted[0]] = splitted[1].rstrip()[1:]
                print("rclone version: " + str(self.rclone_versions))
        return semver.VersionInfo.parse(self.rclone_versions["rclone"])

    def get_sync_version(self):
        """find out the version of the starter in this package"""
        if not self.cfg.enterprise or self.semver > semver.VersionInfo.parse("3.11.99"):
            return semver.VersionInfo.parse("0.0.0")
        if not self.syncer_versions:
            syncer = self.cfg.real_sbin_dir / ("arangosync" + FILE_EXTENSION)
            if not syncer.is_file():
                print("syncer not found where we searched it? " + str(syncer))
                return semver.VersionInfo.parse("0.0.0")
            syncer_version_proc = psutil.Popen(
                [str(syncer), "--version"],
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                universal_newlines=True,
            )
            line = syncer_version_proc.stdout.readline()
            syncer_version_proc.wait()
            print(line)
            string_array = line.split(", ")
            for one_str in string_array:
                splitted = one_str.split(" ")
                self.syncer_versions[splitted[0]] = splitted[1]
                print("ArangoSync version: " + str(self.syncer_versions))
        return semver.VersionInfo.parse(self.syncer_versions["Version"])

    def check_backup_is_created(self):
        """Check that backup was created after package upgrade"""

    def supports_backup(self):
        """Does this installer support automatic backup during minor upgrade?"""
        return False

    def find_crash(self, base_path):
        """search on the disk whether crash files exist"""
        for i in base_path.glob(self.core_glob):
            if str(i).find("node_modules") == -1 and str(i).find("boost") == -1:
                print("Found coredump! " + str(i))
                return True
        return False


class InstallerArchive(InstallerBase, metaclass=ABCMeta):
    """base class for archive packages that need to be installed manually, e.g. .tar.gz for Linux, .zip for Windows"""

    def __init__(self, cfg):
        cfg.have_system_service = False
        cfg.install_prefix = self.basedir
        cfg.bin_dir = None
        cfg.sbin_dir = None
        cfg.real_bin_dir = None
        cfg.real_sbin_dir = None

        cfg.log_dir = Path()
        cfg.dbdir = None
        cfg.appdir = None
        cfg.cfgdir = None

        self.cfg = cfg
        self.cfg.install_prefix = self.basedir
        self.cfg.client_install_prefix = self.basedir
        self.cfg.server_install_prefix = self.basedir
        self.cfg.debug_install_prefix = self.basedir
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None
        self.instance = None
        super().__init__(cfg)

    def supports_hot_backup(self):
        """no hot backup support on the wintendo."""
        if not self.hot_backup:
            return False
        return super().supports_hot_backup()

    def check_service_up(self):
        """nothing to see here"""

    def start_service(self):
        """nothing to see here"""

    def stop_service(self):
        """nothing to see here"""

    @step
    def upgrade_server_package(self, old_installer):
        """Tar installer is the same way we did for installing."""
        self.install_server_package()
        self.calculate_installation_dirs()

    @abstractmethod
    def calculate_installation_dirs(self):
        """calculate installation directories"""

    @step
    def install_server_package_impl(self):
        logging.info("installing Arangodb " + self.installer_type + " server package")
        logging.debug("package dir: {0.cfg.package_dir}- " "server_package: {0.server_package}".format(self))
        if self.cfg.install_prefix.exists():
            print("Flushing pre-existing installation directory: " + str(self.cfg.install_prefix))
            shutil.rmtree(self.cfg.install_prefix)
            while self.cfg.install_prefix.exists():
                print(".")
                time.sleep(1)
        else:
            self.cfg.install_prefix.mkdir(parents=True)

        extract_to = self.cfg.install_prefix / ".."
        extract_to = extract_to.resolve()

        print("extracting: " + str(self.cfg.package_dir / self.server_package) + " to " + str(extract_to))
        shutil.unpack_archive(
            str(self.cfg.package_dir / self.server_package),
            str(extract_to),
        )
        logging.info("Installation successfull")
        self.cfg.server_package_is_installed = True
        self.cfg.install_prefix = self.cfg.server_install_prefix
        self.calculate_installation_dirs()
        self.calculate_file_locations()

    @step
    def install_client_package_impl(self):
        """install the client tar file"""
        logging.info("installing Arangodb " + self.installer_type + "client package")
        logging.debug("package dir: {0.cfg.package_dir}- " "client_package: {0.client_package}".format(self))
        if not self.cfg.install_prefix.exists():
            self.cfg.install_prefix.mkdir(parents=True)
        print(
            "extracting: "
            + str(self.cfg.package_dir / self.client_package)
            + " to "
            + str(self.cfg.install_prefix / "..")
        )
        shutil.unpack_archive(
            str(self.cfg.package_dir / self.client_package),
            str(self.cfg.install_prefix / ".."),
        )
        logging.info("Installation successfull")
        self.cfg.client_package_is_installed = True
        self.cfg.install_prefix = self.cfg.client_install_prefix
        self.calculate_installation_dirs()
        self.calculate_file_locations()

    @step
    def un_install_server_package_impl(self):
        """remove server package"""
        self.purge_install_dir()

    @step
    def un_install_client_package_impl(self):
        """purge client package"""
        self.purge_install_dir()

    @step
    def uninstall_everything_impl(self):
        """uninstall all arango packages present in the system(including those installed outside this installer)"""
        self.purge_install_dir()
        if self.cfg.debug_package_is_installed:
            shutil.rmtree(self.cfg.debug_install_prefix)

    def purge_install_dir(self):
        """remove the install directory"""
        if self.cfg.install_prefix.exists():
            shutil.rmtree(self.cfg.install_prefix)

    def broadcast_bind(self):
        """nothing to see here"""

    def check_engine_file(self):
        """nothing to see here"""

    def check_installed_paths(self):
        """nothing to see here"""

    def cleanup_system(self):
        """nothing to see here"""
