#!/usr/bin/env python3
""" run an Tar installer for the Linux/Mac based operating system """
import platform
import shutil
import logging
from pathlib import Path
import time
import os

from reporting.reporting_utils import step
from arangodb.installers.base import InstallerBase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

MACVER = platform.mac_ver()
WINVER = platform.win32_ver()


class InstallerTAR(InstallerBase):
    """install Tar.gz's on Linux/Mac hosts"""

    # pylint: disable=R0913 disable=R0902
    def __init__(self, cfg):
        self.basedir = Path("/tmp")
        if WINVER[0]:
            self.basedir = Path("C:/tmp")
        if "WORKSPACE_TMP" in os.environ:
            self.basedir = Path(os.environ["WORKSPACE_TMP"])

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
        self.dash = "-"
        self.cfg.install_prefix = self.basedir
        self.extension = "tar.gz"
        self.hot_backup = True
        self.architecture = None

        if MACVER[0]:
            cfg.localhost = "localhost"
            self.remote_package_dir = "MacOSX"
            self.architecture = "macos"
            self.installer_type = ".tar.gz MacOS"
        elif WINVER[0]:
            self.dash = "_"
            cfg.localhost = "localhost"
            self.remote_package_dir = "Windows"
            self.architecture = "win64"
            self.extension = "zip"
            self.hot_backup = False
            self.installer_type = ".zip Windows"
        else:
            self.remote_package_dir = "Linux"
            cfg.localhost = "localhost"
            self.architecture = "linux"
            self.installer_type = ".tar.gz Linux"

        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None
        self.instance = None
        super().__init__(cfg)
        if WINVER[0]:
            self.check_stripped = False
            self.check_symlink = False

    def supports_hot_backup(self):
        """no hot backup support on the wintendo."""
        if not self.hot_backup:
            return False
        return super().supports_hot_backup()

    def calculate_package_names(self):
        enterprise = "e" if self.cfg.enterprise else ""

        semdict = dict(self.cfg.semver.to_dict())
        if semdict["prerelease"]:
            semdict["prerelease"] = "-{prerelease}".format(**semdict)
        else:
            semdict["prerelease"] = ""
        version = "{major}.{minor}.{patch}{prerelease}".format(**semdict)

        self.desc = {
            "ep": enterprise,
            "ver": version,
            "arch": self.architecture,
            "dashus": self.dash,
            "ext": self.extension,
        }
        self.debug_package = None

        if self.architecture == "win64":
            self.server_package = "ArangoDB3{ep}-{ver}{dashus}{arch}.{ext}".format(**self.desc)
            self.client_package = None
            self.cfg.install_prefix = self.basedir / "arangodb3{ep}-{ver}{dashus}{arch}".format(**self.desc)
            self.cfg.bin_dir = self.cfg.install_prefix / "usr" / "bin"
            self.cfg.sbin_dir = self.cfg.install_prefix / "usr" / "bin"
            self.cfg.real_bin_dir = self.cfg.bin_dir
            self.cfg.real_sbin_dir = self.cfg.sbin_dir
        else:
            self.server_package = "arangodb3{ep}-{arch}{dashus}{ver}.{ext}".format(**self.desc)
            self.client_package = "arangodb3{ep}-client-{arch}{dashus}{ver}.{ext}".format(**self.desc)
            if self.cfg.client_package_is_installed:
                self.cfg.install_prefix = self.basedir / "arangodb3{ep}-client-{arch}{dashus}{ver}".format(**self.desc)
            else:
                self.cfg.install_prefix = self.basedir / "arangodb3{ep}-{arch}{dashus}{ver}".format(**self.desc)
            self.cfg.bin_dir = self.cfg.install_prefix / "bin"
            self.cfg.sbin_dir = self.cfg.install_prefix / "usr" / "sbin"
            self.cfg.real_bin_dir = self.cfg.install_prefix / "usr" / "bin"
            self.cfg.real_sbin_dir = self.cfg.sbin_dir
        self.cfg.cfgdir = self.cfg.install_prefix  # n/A
        self.cfg.appdir = self.cfg.install_prefix  # n/A
        self.cfg.dbdir = self.cfg.install_prefix  # n/A
        self.cfg.log_dir = self.cfg.install_prefix  # n/A

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

    @step
    def install_server_package_impl(self):
        logging.info("installing Arangodb " + self.installer_type + "server package")
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

    @step
    def install_client_package_impl(self):
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

    @step
    def un_install_server_package_impl(self):
        self.purge_install_dir()

    @step
    def un_install_client_package_impl(self):
        self.purge_install_dir()

    def purge_install_dir(self):
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
