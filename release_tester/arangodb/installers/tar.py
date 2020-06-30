#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import sys
import time
import os
import shutil
import logging
from pathlib import Path
import psutil
from arangodb.instance import ArangodInstance
from arangodb.installers.base import InstallerBase
from tools.asciiprint import ascii_print
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
import tools.loghelper as lh
import semver


class InstallerTAR(InstallerBase):
    """ install .deb's on debian or ubuntu hosts """
    def __init__(self, cfg):

        self.tar = 'tar'
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
        cfg.localhost = 'ip6-localhost'

        cfg.logDir = None
        cfg.dbdir = None
        cfg.appdir = None
        cfg.cfgdir = None


        super().__init__(cfg)

    def calculate_package_names(self):  
        # Are those required to be stored in the cfg?
        enterprise = 'e' if self.cfg.enterprise else ''
        # package_version = '1'
        architecture = 'linux'

        self.desc = {
            "ep"   : enterprise,
            "ver"  : self.cfg.version,
            # "ver"  : package_version,
            "arch" : architecture
        }
        self.server_package = 'arangodb3{ep}-{arch}-{ver}.tar.gz'.format(**self.desc)
        # self.server_package = 'arangodb3{ep}_{cfg}-{ver}_{arch}.deb'.format(**desc)
        # self.client_package = 'arangodb3{ep}-client_{cfg}-{ver}_{arch}.deb'.format(**desc)
        # self.debug_package = 'arangodb3{ep}-dbg_{cfg}-{ver}_{arch}.deb'.format(**desc)

        self.cfg.installPrefix = Path("/tmp")/'arangodb3{ep}-{ver}'.format(**self.desc)
        self.cfg.bin_dir = self.cfg.installPrefix / "usr" / "bin"     # /usr/bin
        self.cfg.sbin_dir = self.cfg.installPrefix / "usr" / "sbin"   # /usr/sbin
        self.cfg.real_bin_dir = self.cfg.bin_dir
        self.cfg.real_sbin_dir = self.cfg.sbin_dir

    def check_service_up(self):
        pass
        # time.sleep(1)    # TODO
        # print("I am here in: deb.py line: 69")
        # return True

    def start_service(self):
        pass
        # print("I am here in: deb.py line: 73")

        # startserver = pexpect.spawnu('service arangodb3 start')
        # logging.debug("waiting for eof")
        # startserver.expect(pexpect.EOF, timeout=30)
        # while startserver.isalive():
        #     print('.', end='')
        #     if startserver.exitstatus != 0:
        #         raise Exception("server service start didn't"
        #                         "finish successfully!")
        # time.sleep(0.1)
        # self.instance.detect_pid(1) # should be owned by init

    def stop_service(self):
        pass

        # print("I am here in: deb.py line: 88")

        # stopserver = pexpect.spawnu('service arangodb3 stop')
        # logging.debug("waiting for eof")
        # stopserver.expect(pexpect.EOF, timeout=30)
        # while stopserver.isalive():
        #     print('.', end='')
        #     if stopserver.exitstatus != 0:
        #         raise Exception("server service stop didn't"
        #                         "finish successfully!")

    def upgrade_package(self):
       
        # Tar installer is the same way we did for installing.
        self.install_package()
        

    def install_package(self):
        logging.info("installing Arangodb debian Tar package")
        logging.debug("package dir: {0.cfg.package_dir}- server_package: {0.server_package}".format(self))

        cmd = [self.tar, '-xzf', str(self.cfg.package_dir / self.server_package), '-C', '/tmp/']
        lh.log_cmd(cmd)
        install = psutil.Popen(cmd)
        install.wait()
        print()
        logging.info('Installation successfull')

        
    def un_install_package(self):
        pass
        # print("I am here in: deb.py line: 199")

        # uninstall = pexpect.spawnu('dpkg --purge ' +
        #                            'arangodb3' +
        #                            ('e' if self.cfg.enterprise else ''))

        # try:
        #     uninstall.expect('Purging')
        #     ascii_print(uninstall.before)
        #     uninstall.expect(pexpect.EOF)
        #     ascii_print(uninstall.before)
        # except pexpect.exceptions.EOF:
        #     ascii_print(uninstall.before)
        #     sys.exit(1)

    def broadcast_bind(self):
        pass

    def check_engine_file(self):
        pass

    def check_installed_paths(self):
        pass

    def cleanup_system(self):
        pass
        # print("I am here in: deb.py line: 215")
        # # TODO: should this be cleaned by the deb uninstall in first place?
        # if self.cfg.logDir.exists():
        #     shutil.rmtree(self.cfg.logDir)
        # if self.cfg.dbdir.exists():
        #     shutil.rmtree(self.cfg.dbdir)
        # if self.cfg.appdir.exists():
        #     shutil.rmtree(self.cfg.appdir)
        # if self.cfg.cfgdir.exists():
        #     shutil.rmtree(self.cfg.cfgdir)