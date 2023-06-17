#!/usr/bin/env python3
""" installer for .zip packages on Windows """
# pylint: disable=import-error
import os
from pathlib import Path
import semver


# pylint: disable=unused-import
# this will patch psutil for us:
from arangodb.installers.base import InstallerArchive
from arangodb.installers.windows import InstallerWin


class InstallerZip(InstallerArchive, InstallerWin):
    """installer for .zip packages on Windows"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=too-many-statements
    def __init__(self, cfg):
        self.basedir = Path("C:/tmp")
        if "WORKSPACE_TMP" in os.environ:
            self.basedir = Path(os.environ["WORKSPACE_TMP"])
        self.extension = "zip"
        self.hot_backup = False
        self.dash = "_"
        cfg.localhost = "localhost"
        self.remote_package_dir = "Windows"
        self.operating_system = "win64"
        if cfg.semver > semver.VersionInfo.parse("3.9.99"):
            self.arch = "_amd64"
            self.arch = ""
        else:
            self.arch = ""
        self.extension = "zip"
        self.hot_backup = False
        self.installer_type = ".zip Windows"
        super().__init__(cfg)
        self.check_symlink = False
        self.core_glob = "**/*.dmp"
        self.test_dir = self.cfg.install_prefix

    def calculate_package_names(self):
        enterprise = "e" if self.cfg.enterprise else ""

        semdict = dict(self.cfg.semver.to_dict())
        if semdict["prerelease"]:
            if semdict["prerelease"].startswith("rc"):
                semdict["prerelease"] = "-" + semdict["prerelease"].replace("rc", "rc.").replace("..", ".")
            else:
                semdict["prerelease"] = "-{prerelease}".format(**semdict)
        else:
            semdict["prerelease"] = ""
        version = "{major}.{minor}.{patch}{prerelease}".format(**semdict)

        self.desc = {
            "ep": enterprise,
            "ver": version,
            "os": self.operating_system,
            "arch": self.arch,
            "dashus": self.dash,
            "ext": self.extension,
        }
        self.debug_package = None

        self.server_package = "ArangoDB3{ep}-{ver}{dashus}{os}{arch}.{ext}".format(**self.desc)
        self.debug_package = "ArangoDB3{ep}-{ver}.pdb.{ext}".format(**self.desc)
        self.client_package = None
        self.cfg.install_prefix = self.basedir / "arangodb3{ep}-{ver}{dashus}{os}{arch}".format(**self.desc)
        self.cfg.bin_dir = self.cfg.install_prefix / "usr" / "bin"
        self.cfg.sbin_dir = self.cfg.install_prefix / "usr" / "bin"
        self.cfg.real_bin_dir = self.cfg.bin_dir
        self.cfg.real_sbin_dir = self.cfg.sbin_dir
        self.cfg.cfgdir = self.cfg.install_prefix  # n/A
        self.cfg.appdir = self.cfg.install_prefix  # n/A
        self.cfg.dbdir = self.cfg.install_prefix  # n/A
        self.cfg.log_dir = self.cfg.install_prefix  # n/A

    def calculate_installation_dirs(self):
        self.cfg.bin_dir = self.test_dir / "usr" / "bin"
        self.cfg.sbin_dir = self.test_dir / "usr" / "bin"
        self.cfg.real_bin_dir = self.cfg.bin_dir
        self.cfg.real_sbin_dir = self.cfg.sbin_dir
