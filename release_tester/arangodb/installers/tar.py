#!/usr/bin/env python3
""" run an Tar installer for the Linux/Mac based operating system """
import platform
import shutil
import logging
from pathlib import Path
import os

from reporting.reporting_utils import step
from arangodb.installers.base import InstallerBase
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

MACVER = platform.mac_ver()
WINVER = platform.win32_ver()

class InstallerTAR(InstallerBase):
    """ install Tar.gz's on Linux/Mac hosts """
# pylint: disable=R0913 disable=R0902
    def __init__(self, cfg):
        BASEDIR = Path("/tmp")
        if WINVER[0]:
            BASEDIR = Path("C:/tmp")
        print(os.environ)
        if "WORKSPACE_TMP" in os.environ:
            print("snatoheusanoetuh")
            BASEDIR=Path(os.environ["WORKSPACE_TMP"])
            print(BASEDIR)
        
        BASEDIR=Path(os.environ["WORKSPACE_TMP"])
        cfg.have_system_service = False

        cfg.install_prefix = BASEDIR
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
        self.cfg.install_prefix = BASEDIR
        self.extension = 'tar.gz'
        self.hot_backup = True
        self.architecture = None

        if MACVER[0]:
            cfg.localhost = 'localhost'
            self.remote_package_dir  = 'MacOSX'
            self.architecture = 'macos'
            self.installer_type = ".tar.gz MacOS"
        elif WINVER[0]:
            self.dash = "_"
            cfg.localhost = 'localhost'
            self.remote_package_dir  = 'Windows'
            self.architecture = 'win64'
            self.extension = 'zip'
            self.hot_backup = False
            self.installer_type = ".zip Windows"
        else:
            self.remote_package_dir  = 'Linux'
            cfg.localhost = 'localhost'
            self.architecture = 'linux'
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
        """ no hot backup support on the wintendo. """
        if not self.hot_backup:
            return False
        return super().supports_hot_backup()

    def calculate_package_names(self):
        enterprise = 'e' if self.cfg.enterprise else ''

        semdict = dict(self.cfg.semver.to_dict())
        if semdict['prerelease']:
            semdict['prerelease'] = '-{prerelease}'.format(**semdict)
        else:
            semdict['prerelease'] = ''
        version = '{major}.{minor}.{patch}{prerelease}'.format(**semdict)

        self.desc = {
            "ep"   : enterprise,
            "ver"  : version,
            "arch" : self.architecture,
            "dashus" : self.dash,
            "ext" : self.extension
        }
        self.debug_package = None
        self.client_package = None
        if self.architecture == 'win64':
            self.server_package = 'ArangoDB3{ep}-{ver}{dashus}{arch}.{ext}'.format(**self.desc)
            self.cfg.install_prefix = Path(os.environ["WORKSPACE_TMP"]) / \
                'arangodb3{ep}-{ver}{dashus}{arch}'.format(**self.desc)
            self.cfg.bin_dir = self.cfg.install_prefix / "usr" / "bin"
            self.cfg.sbin_dir = self.cfg.install_prefix / "usr" / "bin"
            self.cfg.real_bin_dir = self.cfg.bin_dir
            self.cfg.real_sbin_dir = self.cfg.sbin_dir
        else:
            self.server_package = 'arangodb3{ep}-{arch}{dashus}{ver}.{ext}'.format(**self.desc)
            self.cfg.install_prefix = Path("/tmp") / \
                'arangodb3{ep}-{arch}{dashus}{ver}'.format(**self.desc)
            self.cfg.bin_dir = self.cfg.install_prefix / "bin"
            self.cfg.sbin_dir = self.cfg.install_prefix / "usr" / "sbin"
            self.cfg.real_bin_dir = self.cfg.install_prefix / "usr" / "bin"
            self.cfg.real_sbin_dir = self.cfg.sbin_dir
        self.cfg.cfgdir = self.cfg.install_prefix # n/A
        self.cfg.appdir = self.cfg.install_prefix # n/A
        self.cfg.dbdir = self.cfg.install_prefix # n/A
        self.cfg.log_dir = self.cfg.install_prefix # n/A

    def check_service_up(self):
        """ nothing to see here """

    def start_service(self):
        """ nothing to see here """

    def stop_service(self):
        """ nothing to see here """

    @step
    def upgrade_package(self, old_installer):
        """ Tar installer is the same way we did for installing."""
        self.install_package()

    @step
    def install_package(self):
        logging.info("installing Arangodb " + self.installer_type + " package")
        logging.debug(
            "package dir: {0.cfg.package_dir}- "
            "server_package: {0.server_package}".format(self))
        # self.cfg.install_prefix = Path(os.environ["WORKSPACE_TMP"])
        if not self.cfg.install_prefix.exists():
            self.cfg.install_prefix.mkdir()
        shutil.unpack_archive(str(self.cfg.package_dir / self.server_package),
                              str(self.cfg.install_prefix / '..'))
        logging.info('Installation successfull')

    @step
    def un_install_package(self):
        if self.cfg.install_prefix.exists():
            shutil.rmtree(self.cfg.install_prefix)

    def broadcast_bind(self):
        """ nothing to see here """

    def check_engine_file(self):
        """ nothing to see here """

    def check_installed_paths(self):
        """ nothing to see here """

    def cleanup_system(self):
        """ nothing to see here """
