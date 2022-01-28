#!/usr/bin/env python3
"""
 this installer expects to be running inside the arango
 docker container via derived containers etc.
"""
import logging
from pathlib import Path
import semver
from arangodb.installers.base import InstallerBase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


class InstallerDocker(InstallerBase):
    """run inside docker"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes
    def __init__(self, cfg):
        cfg.localhost = "ip6-localhost"

        self.hot_backup = True
        self.check_stripped = True
        self.check_symlink = True
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None
        self.instance = None
        self.installer_type = "Docker"
        version = cfg.version.split("~")[0]
        version = ".".join(version.split(".")[:3])
        self.semver = semver.VersionInfo.parse(version)

        cfg.have_system_service = False
        cfg.base_test_dir = Path("/home/testdata")
        cfg.install_prefix = None
        cfg.bin_dir = Path("/usr/bin")
        cfg.sbin_dir = Path("/usr/sbin")
        cfg.real_bin_dir = Path("/usr/bin")
        cfg.real_sbin_dir = Path("/usr/sbin")

        cfg.log_dir = Path()
        cfg.dbdir = None
        cfg.appdir = None
        cfg.cfgdir = None

        super().__init__(cfg)

    def calculate_package_names(self):
        enterprise = "e" if self.cfg.enterprise else ""
        architecture = "linux"
        semdict = dict(self.cfg.semver.to_dict())
        if semdict["prerelease"]:
            semdict["prerelease"] = "-{prerelease}".format(**semdict)
        else:
            semdict["prerelease"] = ""
        version = "{major}.{minor}.{patch}{prerelease}".format(**semdict)

        self.desc = {"ep": enterprise, "ver": version, "arch": architecture}

        self.server_package = None
        self.debug_package = None
        self.client_package = None
        self.cfg.cfgdir = self.cfg.install_prefix  # n/A
        self.cfg.appdir = self.cfg.install_prefix  # n/A
        self.cfg.dbdir = self.cfg.install_prefix  # n/A
        self.cfg.log_dir = self.cfg.install_prefix  # n/A

    def check_service_up(self):
        pass

    def start_service(self):
        pass

    def stop_service(self):
        pass

    def upgrade_server_package(self, old_installer):
        pass

    def install_server_package_impl(self):
        logging.info("not installing anything.")

    def un_install_server_package_impl(self):
        pass

    def install_client_package_impl(self):
        """ no docker client container """

    def  un_install_client_package_impl(self):
        """ no docker client container """

    def broadcast_bind(self):
        pass

    def check_engine_file(self):
        pass

    def check_installed_paths(self):
        pass

    def cleanup_system(self):
        pass
