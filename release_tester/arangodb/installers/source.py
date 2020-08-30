#!/usr/bin/env python3

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


class InstallerSRC(InstallerBase):
    """ wraps source directory with build inside """
    def __init__(self, cfg):
        self.tar = 'tar'
        macver = platform.mac_ver()
        self.remote_package_dir  = 'Linux'
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
        cfg.bin_dir = cfg.package_dir / cfg.mode / 'bin'
        cfg.sbin_dir = cfg.bin_dir
        cfg.real_bin_dir = cfg.bin_dir
        cfg.real_sbin_dir = cfg.bin_dir

        cfg.logDir = Path()
        cfg.cfgdir = cfg.package_dir / 'etc' / 'relative'
        print(cfg.cfgdir)
        cfg.appdir = None

        super().__init__(cfg)
        print(self.cfg.cfgdir)

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
        #self.cfg.installPrefix = Path("/tmp") / 'arangodb3{ep}-{ver}'.format(**self.desc)
        #self.cfg.bin_dir = self.cfg.installPrefix / "bin"
        #self.cfg.sbin_dir = self.cfg.installPrefix / "usr" / "sbin"
        #self.cfg.real_bin_dir = self.cfg.installPrefix / "usr" / "bin"
        #self.cfg.real_sbin_dir = self.cfg.sbin_dir

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
        pass
   
    def un_install_package(self):
        pass

    def broadcast_bind(self):
        pass

    def check_engine_file(self):
        pass

    def check_installed_paths(self):
        pass

    def cleanup_system(self):
        pass
