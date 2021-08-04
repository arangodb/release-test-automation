#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import sys
import time
import os
import shutil
import logging
from pathlib import Path

from reporting.reporting_utils import step
import pexpect
import semver
from arangodb.installers.linux import InstallerLinux
from tools.asciiprint import ascii_print, print_progress as progress
import tools.loghelper as lh
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class InstallerDeb(InstallerLinux):
    """ install .deb's on debian or ubuntu hosts """
    def __init__(self, cfg):
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None
        self.installer_type = "DEB"

        # Are those required to be stored in the cfg?
        cfg.installPrefix = Path("/")
        cfg.bin_dir = cfg.installPrefix / "usr" / "bin"
        cfg.sbin_dir = cfg.installPrefix / "usr" / "sbin"
        cfg.real_bin_dir = cfg.bin_dir
        cfg.real_sbin_dir = cfg.sbin_dir
        cfg.localhost = 'localhost'

        cfg.log_dir = Path('/var/log/arangodb3')
        cfg.dbdir = Path('/var/lib/arangodb3')
        cfg.appdir = Path('/var/lib/arangodb3-apps')
        cfg.cfgdir = Path('/etc/arangodb3')


        super().__init__(cfg)

    def calculate_package_names(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        package_version = '1'
        architecture = 'amd64'

        semdict = dict(self.cfg.semver.to_dict())

        if semdict['prerelease']:
            if semdict['prerelease'].startswith('rc'):
                semdict['prerelease'] = '~{prerelease}'.format(**semdict)
            else:
                semdict['prerelease'] = '~~{prerelease}'.format(**semdict)
        else:
            semdict['prerelease'] = ''

        version = '{major}.{minor}.{patch}{prerelease}'.format(**semdict)

        desc = {
            "ep"   : enterprise,
            "cfg"  : version,
            "ver"  : package_version,
            "arch" : architecture
        }

        self.server_package = (
            'arangodb3{ep}_{cfg}-{ver}_{arch}.deb'.format(**desc))
        self.client_package = (
            'arangodb3{ep}-client_{cfg}-{ver}_{arch}.deb'.format(**desc))
        self.debug_package = (
            'arangodb3{ep}-dbg_{cfg}-{ver}_{arch}.deb'.format(**desc))

    def start_service(self):
        startserver = pexpect.spawnu('service arangodb3 start')
        logging.debug("waiting for eof")
        startserver.expect(pexpect.EOF, timeout=30)
        while startserver.isalive():
            progress('.')
            if startserver.exitstatus != 0:
                raise Exception("server service start didn't"
                                "finish successfully!")
        time.sleep(0.1)
        self.instance.detect_pid(1) # should be owned by init

    def stop_service(self):
        stopserver = pexpect.spawnu('service arangodb3 stop')
        logging.debug("waiting for eof")
        stopserver.expect(pexpect.EOF, timeout=30)
        while stopserver.isalive():
            progress('.')
            if stopserver.exitstatus != 0:
                raise Exception("server service stop didn't"
                                "finish successfully!")

    @step
    def upgrade_package(self, old_installer):
        logging.info("upgrading Arangodb debian package")
        os.environ['DEBIAN_FRONTEND'] = 'readline'
        cmd = 'dpkg -i ' + str(self.cfg.package_dir / self.server_package)
        lh.log_cmd(cmd)
        server_upgrade = pexpect.spawnu(cmd)
        while True:
            try:
                i = server_upgrade.expect([
                    'Upgrading database files',
                    'Database files are up-to-date',
                    'arangod.conf'],
                                          timeout=60)
                if i == 0:
                    logging.info("X" * 80)
                    ascii_print(server_upgrade.before)
                    logging.info("X" * 80)
                    logging.info("[X] Upgrading database files")
                    break
                if i == 1:
                    logging.info("X" * 80)
                    ascii_print(server_upgrade.before)
                    logging.info("X" * 80)
                    logging.info("[ ] Update not needed.")
                    break
                if i == 2: # modified arangod.conf...
                    ascii_print(server_upgrade.before)
                    server_upgrade.sendline('Y')
                    # fallthrough - repeat.
            except pexpect.exceptions.EOF:
                logging.info("X" * 80)
                ascii_print(server_upgrade.before)
                logging.info("X" * 80)
                logging.info("[E] Upgrade failed!")
                sys.exit(1)
        try:
            logging.info("waiting for the upgrade to finish")
            server_upgrade.expect(pexpect.EOF, timeout=30)
            ascii_print(server_upgrade.before)
        except pexpect.exceptions.EOF:
            logging.info("TIMEOUT!")

    @step
    def install_package(self):
        # pylint: disable=too-many-statements
        logging.info("installing Arangodb debian package")
        server_not_started = False
        os.environ['DEBIAN_FRONTEND'] = 'readline'
        self.cfg.passvoid = "DEB_passvoid_%d" % os.getpid()
        logging.debug("package dir: {0.cfg.package_dir}- "
                      "server_package: {0.server_package}".format(self))
        cmd = 'dpkg -i ' + str(self.cfg.package_dir / self.server_package)
        lh.log_cmd(cmd)
        server_install = pexpect.spawnu(cmd)
        try:
            logging.debug("expect: user1")
            i = server_install.expect(['user:', 'arangod.conf'], timeout=120)
            # there are remaints of previous installations.
            # We overwrite existing config files.
            if i == 1:
                server_install.sendline('Y')
                ascii_print(server_install.before)
                server_install.expect('user:')
            ascii_print(server_install.before)
            logging.debug("expect: setting password: "
                          "{0.cfg.passvoid}".format(self))
            server_install.sendline(self.cfg.passvoid)

            logging.debug("expect: user2")
            server_install.expect('user:')
            ascii_print(server_install.before)
            logging.debug("expect: setting password: "
                          "{0.cfg.passvoid}".format(self))
            server_install.sendline(self.cfg.passvoid)

            logging.debug("expect: upgrade behaviour selection")
            server_install.expect([
                "Automatically upgrade database files",
                "automatically upgraded"])
            ascii_print(server_install.before)
            server_install.sendline("yes")


            if self.cfg.semver <= semver.VersionInfo.parse("3.6.99"):
                logging.debug("expect: storage engine selection")
                server_install.expect("Database storage engine")
                ascii_print(server_install.before)
                server_install.sendline("1")


            logging.debug("expect: backup selection")
            server_install.expect("Backup database files before upgrading")
            ascii_print(server_install.before)
            server_install.sendline("no")
        except pexpect.exceptions.EOF:
            lh.line("X")
            ascii_print(server_install.before)
            lh.line("X")
            logging.error("Installation failed!")
            sys.exit(1)
        try:
            logging.info("waiting for the installation to finish")
            server_install.expect(pexpect.EOF, timeout=30)
            ascii_print(server_install.before)
            server_not_started = server_install.before.find(
                "not running 'is-active arangodb3.service'") >= 0
        except pexpect.exceptions.EOF:
            logging.info("TIMEOUT!")
        while server_install.isalive():
            progress('.')
            if server_install.exitstatus != 0:
                raise Exception(
                    "server installation didn't finish successfully!")
        print()
        logging.info('Installation successfull')
        self.set_system_instance()
        if server_not_started:
            logging.info('Environment did not start arango service,'
                         'doing this now!')
            self.start_service()
        self.instance.detect_pid(1) # should be owned by init

    @step
    def un_install_package(self):
        cmd = ('dpkg --purge ' + 'arangodb3' +
               ('e' if self.cfg.enterprise else ''))
        lh.log_cmd(cmd)
        uninstall = pexpect.spawnu(cmd)
        try:
            uninstall.expect(['Purging','which isn\'t installed'])
            ascii_print(uninstall.before)
            uninstall.expect(pexpect.EOF)
            ascii_print(uninstall.before)
        except pexpect.exceptions.EOF:
            ascii_print(uninstall.before)
            sys.exit(1)

    @step
    def install_debug_package(self):
        """ installing debug package """
        cmd = 'dpkg -i ' + str(self.cfg.package_dir / self.debug_package)
        lh.log_cmd(cmd)
        os.environ['DEBIAN_FRONTEND'] = 'readline'
        debug_install = pexpect.spawnu(cmd)
        try:
            logging.info("waiting for the installation to finish")
            debug_install.expect(pexpect.EOF, timeout=60)
        except pexpect.exceptions.EOF:
            logging.info("TIMEOUT!")
            debug_install.close(force=True)
            ascii_print(debug_install.before)
        print()
        logging.info(str(self.debug_package) + ' Installation successfull')
        self.cfg.have_debug_package = True

        while debug_install.isalive():
            progress('.')
            if debug_install.exitstatus != 0:
                debug_install.close(force=True)
                ascii_print(debug_install.before)
                raise Exception(
                    str(self.debug_package) +
                    " debug installation didn't finish successfully!")
        return self.cfg.have_debug_package

    @step
    def un_install_debug_package(self):
        os.environ['DEBIAN_FRONTEND'] = 'readline'
        cmd = ('dpkg --purge ' + 'arangodb3' +
               ('e-dbg' if self.cfg.enterprise else '-dbg'))
        lh.log_cmd(cmd)
        uninstall = pexpect.spawnu(cmd)
        try:
            uninstall.expect(['Removing','which isn\'t installed'])
            ascii_print(uninstall.before)
            uninstall.expect(pexpect.EOF, timeout=30)
            ascii_print(uninstall.before)
        except pexpect.exceptions.EOF:
            ascii_print(uninstall.before)
            sys.exit(1)

        while uninstall.isalive():
            progress('.')
            if uninstall.exitstatus != 0:
                uninstall.close(force=True)
                ascii_print(uninstall.before)
                raise Exception(
                    "Debug package uninstallation didn't finish successfully!")

    @step
    def cleanup_system(self):
        if self.cfg.log_dir.exists():
            shutil.rmtree(self.cfg.log_dir)
        if self.cfg.dbdir.exists():
            shutil.rmtree(self.cfg.dbdir)
        if self.cfg.appdir.exists():
            shutil.rmtree(self.cfg.appdir)
        if self.cfg.cfgdir.exists():
            shutil.rmtree(self.cfg.cfgdir)
