#!/usr/bin/env python3
""" run an Tar installer for the Linux/Mac based operating system """
import platform
import shutil
import logging
from pathlib import Path
import psutil
import semver
import tools.loghelper as lh
from arangodb.installers.base import InstallerBase
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class InstallerTAR(InstallerBase):
    """ install Tar.gz's on Linux/Mac hosts """
    def __init__(self, cfg):
        macver = platform.mac_ver()
        if macver[0]:
            self.tar = 'gtar'
            cfg.localhost = 'localhost'
        else:
            self.tar = 'tar'
            cfg.localhost = 'ip6-localhost'

        self.check_stripped = True
        self.check_symlink = True
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None
        version = cfg.version.split("~")[0]
        version = ".".join(version.split(".")[:3])
        self.semver = semver.VersionInfo.parse(version)

        cfg.have_system_service = False
        cfg.baseTestDir = Path('/tmp')
        cfg.installPrefix = None
        cfg.bin_dir = None
        cfg.sbin_dir = None
        cfg.real_bin_dir = None
        cfg.real_sbin_dir = None

        cfg.logDir = Path()
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

        self.desc = {
            "ep"   : enterprise,
            "ver"  : self.cfg.version,
            "arch" : architecture
        }

        self.server_package = 'arangodb3{ep}-{arch}-{ver}.tar.gz'.format(**self.desc)
        self.cfg.installPrefix = Path("/tmp") / 'arangodb3{ep}-{ver}'.format(**self.desc)
        self.cfg.bin_dir = self.cfg.installPrefix / "bin"
        self.cfg.sbin_dir = self.cfg.installPrefix / "usr" / "sbin"  
        self.cfg.real_bin_dir = self.cfg.installPrefix / "usr" / "bin"
        self.cfg.real_sbin_dir = self.cfg.sbin_dir

    def check_service_up(self):
        pass

    def start_service(self):
        pass

    def stop_service(self):
        pass

    def upgrade_package(self):
        """ Tar installer is the same way we did for installing."""
        self.install_package()

    def install_package(self):
        logging.info("installing Arangodb debian Tar package")
        logging.debug("package dir: {0.cfg.package_dir}- server_package: {0.server_package}".format(self))

        cmd = [self.tar,
                   '-xzf',
                   str(self.cfg.package_dir / self.server_package),
                   '-C',
                   '/tmp/']
        lh.log_cmd(cmd)
        install = psutil.Popen(cmd)
        install.wait()
        print()
        logging.info('Installation successfull')

    def un_install_package(self):
        shutil.rmtree(self.cfg.installPrefix)

    def broadcast_bind(self):
        pass

    def check_engine_file(self):
        pass

    def check_installed_paths(self):
        pass

    def cleanup_system(self):
        pass
