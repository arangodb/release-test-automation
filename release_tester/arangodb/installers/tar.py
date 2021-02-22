#!/usr/bin/env python3
""" run an Tar installer for the Linux/Mac based operating system """
import platform
import shutil
import logging
from pathlib import Path
import psutil
import tools.loghelper as lh
from arangodb.installers.base import InstallerBase
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class InstallerTAR(InstallerBase):
    """ install Tar.gz's on Linux/Mac hosts """
# pylint: disable=R0913 disable=R0902
    def __init__(self, cfg):
        self.tar = 'tar'
        macver = platform.mac_ver()
        if macver[0]:
            cfg.localhost = 'localhost'
            self.remote_package_dir  = 'MacOSX'
        else:
            self.remote_package_dir  = 'Linux'
            cfg.localhost = 'localhost'

        self.hot_backup = True
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None
        self.instance = None

        cfg.have_system_service = False

        cfg.installPrefix = None
        cfg.bin_dir = None
        cfg.sbin_dir = None
        cfg.real_bin_dir = None
        cfg.real_sbin_dir = None

        cfg.log_dir = Path()
        cfg.dbdir = None
        cfg.appdir = None
        cfg.cfgdir = None

        super().__init__(cfg)

    def calculate_package_names(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        architecture = 'linux'
        macver = platform.mac_ver()
        if macver[0]:
            architecture = 'macos'

        semdict = dict(self.cfg.semver.to_dict())
        if semdict['prerelease']:
            semdict['prerelease'] = '-{prerelease}'.format(**semdict)
        else:
            semdict['prerelease'] = ''
        version = '{major}.{minor}.{patch}{prerelease}'.format(**semdict)

        self.desc = {
            "ep"   : enterprise,
            "ver"  : version,
            "arch" : architecture
        }

        self.server_package = 'arangodb3{ep}-{arch}-{ver}.tar.gz'.format(**self.desc)
        self.debug_package = None
        self.client_package = None
        self.cfg.installPrefix = Path("/tmp") / 'arangodb3{ep}-{ver}'.format(**self.desc)
        self.cfg.bin_dir = self.cfg.installPrefix / "bin"
        self.cfg.sbin_dir = self.cfg.installPrefix / "usr" / "sbin"
        self.cfg.real_bin_dir = self.cfg.installPrefix / "usr" / "bin"
        self.cfg.real_sbin_dir = self.cfg.sbin_dir
        self.cfg.cfgdir = self.cfg.installPrefix # n/A
        self.cfg.appdir = self.cfg.installPrefix # n/A
        self.cfg.dbdir = self.cfg.installPrefix # n/A
        self.cfg.log_dir = self.cfg.installPrefix # n/A

    def check_service_up(self):
        pass

    def start_service(self):
        pass

    def stop_service(self):
        pass

    def upgrade_package(self, old_installer):
        """ Tar installer is the same way we did for installing."""
        self.install_package()

    def install_package(self):
        logging.info("installing Arangodb debian Tar package")
        logging.debug(
            "package dir: {0.cfg.package_dir}- "
            "server_package: {0.server_package}".format(self))

        self.cfg.installPrefix.mkdir()
        cmd = [self.tar,
                   '-xf', str(self.cfg.package_dir / self.server_package),
                   '-C',  str(self.cfg.installPrefix),
                   '--strip-components', '1'
               ]
        lh.log_cmd(cmd)
        install = psutil.Popen(cmd)
        if install.wait() != 0:
            raise Exception("extracting the Archive failed!")
        print()
        logging.info('Installation successfull')

    def un_install_package(self):
        if self.cfg.installPrefix.exists():
            shutil.rmtree(self.cfg.installPrefix)

    def broadcast_bind(self):
        pass

    def check_engine_file(self):
        pass

    def check_installed_paths(self):
        pass

    def cleanup_system(self):
        pass
