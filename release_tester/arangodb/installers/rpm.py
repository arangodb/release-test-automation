#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import time
import sys
import shutil
import logging
from pathlib import Path
import pexpect
import psutil
from arangodb.sh import ArangoshExecutor
from arangodb.instance import ArangodInstance
from arangodb.installers.base import InstallerBase
from tools.asciiprint import ascii_print

import tools.loghelper as lh


class InstallerRPM(InstallerBase):
    """ install .rpm's on RedHat, Centos or SuSe systems """
    def __init__(self, cfg):
        self.check_stripped = True
        self.check_symlink = True
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.instance = None

        cfg.baseTestDir = Path('/tmp')
        cfg.installPrefix = Path("/")
        cfg.bin_dir = cfg.installPrefix / "usr" / "bin"
        cfg.sbin_dir = cfg.installPrefix / "usr" / "sbin"
        cfg.real_bin_dir = cfg.bin_dir
        cfg.real_sbin_dir = cfg.sbin_dir
        cfg.localhost = 'localhost6'

        super().__init__(cfg)

    def calculate_package_names(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        package_version = '1.0'
        architecture = 'x86_64'

        desc = {
            "ep"   : enterprise,
            "cfg"  : self.cfg.version,
            "ver"  : package_version,
            "arch" : architecture
        }

        self.server_package = 'arangodb3{ep}-{cfg}-{ver}.{arch}.rpm'.format(**desc)
        self.client_package = 'arangodb3{ep}-client-{cfg}-{ver}.{arch}.rpm'.format(**desc)
        self.debug_package = 'arangodb3{ep}-debuginfo-{cfg}-{ver}.{arch}.rpm'.format(**desc)

    def check_service_up(self):
        if self.instance.pid:
            try:
                psutil.Process(self.instance.pid)
            except:
                return False
        else:
            return False
        time.sleep(1)   # TODO
        return True

    def start_service(self):
        assert self.instance

        logging.info("starting service")
        cmd = ['service', 'arangodb3', 'start']
        lh.log_cmd(cmd)
        startserver = psutil.Popen(cmd)
        logging.info("waiting for eof of start service")
        startserver.wait()
        time.sleep(0.1)
        self.instance.detect_pid(1) # should be owned by init

    def stop_service(self):
        logging.info("stopping service")
        cmd = ['service', 'arangodb3', 'stop']
        lh.log_cmd(cmd)
        stopserver = psutil.Popen(cmd)
        logging.info("waiting for eof")
        stopserver.wait()
        while self.check_service_up():
            time.sleep(1)

    def upgrade_package(self):
        logging.info("upgrading Arangodb rpm package")

        self.cfg.passvoid = "sanoetuh"   # TODO
        self.cfg.logDir = Path('/var/log/arangodb3')
        self.cfg.dbdir  = Path('/var/lib/arangodb3')
        self.cfg.appdir = Path('/var/lib/arangodb3-apps')
        self.cfg.cfgdir = Path('/etc/arangodb3')

        self.instance = ArangodInstance("single", "8529", self.cfg.localhost, self.cfg.publicip, self.cfg.installPrefix / self.cfg.logDir)


        #https://access.redhat.com/solutions/1189
        cmd = 'rpm --upgrade ' + str(self.cfg.package_dir / self.server_package)
        lh.log_cmd(cmd)
        server_upgrade = pexpect.spawnu(cmd)

        try:
            server_upgrade.expect('First Steps with ArangoDB:|server will now shut down due to upgrade, database initialization or admin restoration.')
            print(server_upgrade.before)
        except pexpect.exceptions.EOF as exc:
            lh.line("X")
            ascii_print(server_upgrade.before)
            lh.line("X")
            print("exception : " + str(exc))
            lh.line("X")
            logging.error("Upgrade failed!")
            sys.exit(1)

        logging.debug("found: upgrade message")

        logging.info("waiting for the upgrade to finish")
        try:
            server_upgrade.expect(pexpect.EOF, timeout=30)
            ascii_print(server_upgrade.before)
        except pexpect.exceptions.EOF:
            logging.error("TIMEOUT! while upgrading package")
            sys.exit(1)

        logging.debug("upgrade successfully finished")

    def install_package(self):
        self.cfg.logDir = Path('/var/log/arangodb3')
        self.cfg.dbdir  = Path('/var/lib/arangodb3')
        self.cfg.appdir = Path('/var/lib/arangodb3-apps')
        self.cfg.cfgdir = Path('/etc/arangodb3')
        self.instance = ArangodInstance("single", "8529", self.cfg.localhost, self.cfg.publicip, self.cfg.installPrefix / self.cfg.logDir)
        logging.info("installing Arangodb RPM package")
        package = self.cfg.package_dir / self.server_package
        if not package.is_file():
            logging.info("package doesn't exist: %s", str(package))
            raise Exception("failed to find package")

        cmd = 'rpm ' + '-i ' + str(package)
        lh.log_cmd(cmd)
        server_install = pexpect.spawnu(cmd)
        reply = None

        try:
            server_install.expect('the current password is')
            ascii_print(server_install.before)
            server_install.expect(pexpect.EOF, timeout=30)
            reply = server_install.before
            ascii_print(reply)
        except pexpect.exceptions.EOF:
            ascii_print(server_install.before)
            logging.info("Installation failed!")
            sys.exit(1)

        while server_install.isalive():
            print('.', end='')
            if server_install.exitstatus != 0:
                raise Exception("server installation didn't finish successfully!")

        start = reply.find("'")
        end = reply.find("'", start + 1)
        self.cfg.passvoid = reply[start + 1: end]

        self.start_service()
        self.instance.detect_pid(1) # should be owned by init

        pwcheckarangosh = ArangoshExecutor(self.cfg)
        if not pwcheckarangosh.js_version_check():
            logging.error(
                "Version Check failed -"
                "probably setting the default random password didn't work! %s",
                self.cfg.passvoid)

        #should we wait for user here? or mark the error in a special way

        self.stop_service()

        self.cfg.passvoid = "sanoetuh"   # TODO
        lh.log_cmd('/usr/sbin/arango-secure-installation')
        with pexpect.spawnu('/usr/sbin/arango-secure-installation') as etpw:
            result = None
            try:
                ask_for_pass = [
                    'Please enter a new password for the ArangoDB root user:',
                    'Please enter password for root user:',
                ]

                result = etpw.expect(ask_for_pass)
                if result is None:
                    raise RuntimeError("Not asked for password")

                etpw.sendline(self.cfg.passvoid)
                result = etpw.expect('Repeat password: ')
                if result is None:
                    raise RuntimeError("Not asked to repeat the password")
                ascii_print(etpw.before)
                logging.info("password should be set to: " + self.cfg.passvoid)
                etpw.sendline(self.cfg.passvoid)

                logging.info("expecting eof")
                logging.info("password should be set to: " + self.cfg.passvoid)
                result = etpw.expect(pexpect.EOF)

                logging.info("password should be set to: " + self.cfg.passvoid)
                ascii_print(etpw.before)

            #except pexpect.exceptions.EOF:
            except Exception as exc:
                logging.error("setting our password failed!")
                logging.error("X" * 80)
                logging.error("XO" * 80)
                logging.error(repr(self.cfg))
                logging.error("X" * 80)
                logging.error("result: " + str(result))
                logging.error("X" * 80)
                ascii_print(etpw.before)
                logging.error("X" * 80)
                raise exc

        self.start_service()
        self.instance.detect_pid(1) # should be owned by init

    def un_install_package(self):
        cmd = ['rpm', '-e', 'arangodb3' + ('e' if self.cfg.enterprise else '')]
        lh.log_cmd(cmd)
        uninstall = psutil.Popen(cmd)
        uninstall.wait()

    def cleanup_system(self):
        # TODO: should this be cleaned by the rpm uninstall in first place?
        if self.cfg.logDir.exists():
            shutil.rmtree(self.cfg.logDir)
        if self.cfg.dbdir.exists():
            shutil.rmtree(self.cfg.dbdir)
        if self.cfg.appdir.exists():
            shutil.rmtree(self.cfg.appdir)
        if self.cfg.cfgdir.exists():
            shutil.rmtree(self.cfg.cfgdir)
