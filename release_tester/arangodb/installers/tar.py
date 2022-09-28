#!/usr/bin/env python3
""" run an Tar installer for the Linux/Mac based operating system """
import platform
import logging
from pathlib import Path
import os

import semver

from arangodb.installers.base import InstallerArchive

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

MACVER = platform.mac_ver()
WINVER = platform.win32_ver()


class InstallerTAR(InstallerArchive):
    """install Tar.gz's on Linux/Mac hosts"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=too-many-statements
    def __init__(self, cfg):
        self.basedir = Path("/tmp")
        if "WORKSPACE_TMP" in os.environ:
            self.basedir = Path(os.environ["WORKSPACE_TMP"])
        cfg.localhost = "localhost"
        self.extension = "tar.gz"
        if MACVER[0]:
            self.remote_package_dir = "MacOSX"
            self.operating_system = "macos"
            self.installer_type = ".tar.gz MacOS"
        else:
            self.remote_package_dir = "Linux"
            self.operating_system = "linux"
            self.installer_type = ".tar.gz Linux"

        self.architecture = ""
        self.dash = "-"
        self.hot_backup = True

        super().__init__(cfg)

    def calculate_package_names(self):
        if self.cfg.semver > semver.VersionInfo.parse("3.9.99"):
            arch = self.machine
            if arch == 'aarch64':
                arch = 'arm64'
            self.architecture = '_' + arch
        enterprise = "e" if self.cfg.enterprise else ""

        semdict = dict(self.cfg.semver.to_dict())
        if semdict["prerelease"]:
            if semdict["prerelease"].startswith("rc"):
                semdict["prerelease"] = "-" + semdict["prerelease"].replace("rc", "rc.")
            else:
                semdict["prerelease"] = "-{prerelease}".format(**semdict)
        else:
            semdict["prerelease"] = ""
        version = "{major}.{minor}.{patch}{prerelease}".format(**semdict)

        self.desc = {
            "ep": enterprise,
            "ver": version,
            "os": self.operating_system,
            "arch": self.architecture,
            "dashus": self.dash,
            "ext": self.extension,
        }
        print(self.desc)
        self.debug_package = None

        self.server_package = "arangodb3{ep}-{os}{dashus}{ver}{arch}.{ext}".format(**self.desc)
        self.client_package = "arangodb3{ep}-client-{os}{dashus}{ver}{arch}.{ext}".format(**self.desc)
        self.cfg.client_install_prefix = self.basedir / "arangodb3{ep}-client-{arch}{dashus}{ver}".format(**self.desc)
        self.cfg.server_install_prefix = self.basedir / "arangodb3{ep}-{arch}{dashus}{ver}".format(**self.desc)
        if self.cfg.client_package_is_installed:
            self.cfg.install_prefix = self.basedir / "arangodb3{ep}-client-{os}{dashus}{ver}{arch}".format(**self.desc)
        else:
            self.cfg.install_prefix = self.basedir / "arangodb3{ep}-{os}{dashus}{ver}{arch}".format(**self.desc)
        self.cfg.bin_dir = self.cfg.install_prefix / "bin"
        self.cfg.sbin_dir = self.cfg.install_prefix / "usr" / "sbin"
        self.cfg.real_bin_dir = self.cfg.install_prefix / "usr" / "bin"
        self.cfg.real_sbin_dir = self.cfg.sbin_dir
        self.cfg.cfgdir = self.cfg.install_prefix  # n/A
        self.cfg.appdir = self.cfg.install_prefix  # n/A
        self.cfg.dbdir = self.cfg.install_prefix  # n/A
        self.cfg.log_dir = self.cfg.install_prefix  # n/A

    def calculate_installation_dirs(self):
        self.cfg.bin_dir = self.cfg.install_prefix / "bin"
        self.cfg.sbin_dir = self.cfg.install_prefix / "usr" / "sbin"
        self.cfg.real_bin_dir = self.cfg.install_prefix / "usr" / "bin"
        self.cfg.real_sbin_dir = self.cfg.sbin_dir
