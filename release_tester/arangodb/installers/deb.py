#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import time
import os
import sys
import shutil
import logging
from pathlib import Path
import pexpect
from arangodb.log import ArangodLogExaminer
from arangodb.installers.base import InstallerBase
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class InstallerDeb(InstallerBase):
    """ install .deb's on debian or ubuntu hosts """
    def __init__(self, install_config):
        self.cfg = install_config
        self.cfg.baseTestDir = Path('/tmp')
        self.cfg.installPrefix = Path("/")
        self.cfg.bin_dir = self.cfg.installPrefix / "usr" / "bin"
        self.cfg.sbin_dir = self.cfg.installPrefix / "usr" / "sbin"
        self.caclulate_file_locations()
        self.cfg.localhost = 'ip6-localhost'
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None
        self.cfg.logDir = Path('/var/log/arangodb3')
        self.cfg.dbdir = Path('/var/lib/arangodb3')
        self.cfg.appdir = Path('/var/lib/arangodb3-apps')
        self.cfg.cfgdir = Path('/etc/arangodb3')

    def calculate_package_names(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        package_version = '1'
        architecture = 'amd64'

        desc = {
            "ep"   : enterprise,
            "cfg"  : self.cfg.version,
            "ver"  : package_version,
            "arch" : architecture
        }

        self.server_package = 'arangodb3{ep}_{cfg}-{ver}_{arch}.deb'.format(**desc)
        self.client_package = 'arangodb3{ep}-client_{cfg}-{ver}_{arch}.deb'.format(**desc)
        self.debug_package = 'arangodb3{ep}-dbg_{cfg}-{ver}_{arch}.deb'.format(**desc)

    def check_service_up(self):
        time.sleep(1)    # TODO
        return True

    def start_service(self):
        startserver = pexpect.spawnu('service arangodb3 start')
        logging.info("waiting for eof")
        startserver.expect(pexpect.EOF, timeout=30)
        while startserver.isalive():
            logging.info('.')
            if startserver.exitstatus != 0:
                raise Exception("server service start didn't"
                                "finish successfully!")
        time.sleep(0.1)
        self.log_examiner.detect_instance_pids()

    def stop_service(self):
        stopserver = pexpect.spawnu('service arangodb3 stop')
        logging.info("waiting for eof")
        stopserver.expect(pexpect.EOF, timeout=30)
        while stopserver.isalive():
            logging.info('.')
            if stopserver.exitstatus != 0:
                raise Exception("server service stop didn't"
                                "finish successfully!")

    def upgrade_package(self):
        logging.info("installing Arangodb debian package")
        os.environ['DEBIAN_FRONTEND'] = 'readline'
        server_upgrade = pexpect.spawnu('dpkg -i ' +
                                        str(self.cfg.package_dir / self.server_package))
        try:
            server_upgrade.expect('Upgrading database files')
            print(server_upgrade.before)
        except pexpect.exceptions.EOF:
            logging.info("X" * 80)
            print(server_upgrade.before)
            logging.info("X" * 80)
            logging.info("Upgrade failed!")
            sys.exit(1)
        try:
            logging.info("waiting for the upgrade to finish")
            server_upgrade.expect(pexpect.EOF, timeout=30)
            print(server_upgrade.before)
        except pexpect.exceptions.EOF:
            logging.info("TIMEOUT!")

    def install_package(self):
        self.cfg.all_instances = {
            'single': {
                'logfile': self.cfg.installPrefix / self.cfg.logDir / 'arangod.log'
            }
        }
        logging.info("installing Arangodb debian package")
        os.environ['DEBIAN_FRONTEND'] = 'readline'
        server_install = pexpect.spawnu('dpkg -i ' +
                                        str(self.cfg.package_dir / self.server_package))
        try:
            server_install.expect('user:')
            print(server_install.before)
            server_install.sendline(self.cfg.passvoid)
            server_install.expect('user:')
            print(server_install.before)
            server_install.sendline(self.cfg.passvoid)
            server_install.expect("Automatically upgrade database files")
            print(server_install.before)
            server_install.sendline("yes")
            server_install.expect("Database storage engine")
            print(server_install.before)
            server_install.sendline("1")
            server_install.expect("Backup database files before upgrading")
            print(server_install.before)
            server_install.sendline("no")
        except pexpect.exceptions.EOF:
            logging.info("X" * 80)
            print(server_install.before)
            logging.info("X" * 80)
            logging.info("Installation failed!")
            sys.exit(1)
        try:
            logging.info("waiting for the installation to finish")
            server_install.expect(pexpect.EOF, timeout=30)
            print(server_install.before)
        except pexpect.exceptions.EOF:
            logging.info("TIMEOUT!")
        while server_install.isalive():
            logging.info('.')
            if server_install.exitstatus != 0:
                raise Exception("server installation didn't finish successfully!")
        logging.info('Installation successfull')
        self.log_examiner = ArangodLogExaminer(self.cfg)
        self.log_examiner.detect_instance_pids()

    def un_install_package(self):
        uninstall = pexpect.spawnu('dpkg --purge ' +
                                   'arangodb3' +
                                   ('e' if self.cfg.enterprise else ''))

        try:
            uninstall.expect('Purging')
            print(uninstall.before)
            uninstall.expect(pexpect.EOF)
            print(uninstall.before)
        except pexpect.exceptions.EOF:
            print(uninstall.before)
            sys.exit(1)

    def cleanup_system(self):
        # TODO: should this be cleaned by the deb uninstall in first place?
        if self.cfg.logDir.exists():
            shutil.rmtree(self.cfg.logDir)
        if self.cfg.dbdir.exists():
            shutil.rmtree(self.cfg.dbdir)
        if self.cfg.appdir.exists():
            shutil.rmtree(self.cfg.appdir)
        if self.cfg.cfgdir.exists():
            shutil.rmtree(self.cfg.cfgdir)
