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
from arangodb.log import ArangodLogExaminer
from arangodb.installers.base import InstallerBase
from pprint import pprint as PP
from pprint import pformat as PF

import obi.util.logging_helper as lh

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class InstallerRPM(InstallerBase, lh.LoggedBase):
    """ install .rpm's on RedHat, Centos or SuSe systems """
    def __init__(self, install_config):
        self.cfg = install_config
        self.cfg.baseTestDir = Path('/tmp')
        self.cfg.installPrefix = Path("/")
        self.cfg.bin_dir = self.cfg.installPrefix / "usr" / "bin"
        self.cfg.sbin_dir = self.cfg.installPrefix / "usr" / "sbin"
        self.caclulate_file_locations()
        self.cfg.localhost = 'localhost6'
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None

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
        if 'PID' in self.cfg.all_instances['single']:
            try:
                psutil.Process(self.cfg.all_instances.single['PID'])
            except:
                return False
        else:
            return False
        time.sleep(1)   # TODO
        return True

    def start_service(self):
        logging.info("STARTING SERVICE")
        startserver = psutil.Popen(['service', 'arangodb3', 'start'])
        logging.info("waiting for eof")
        startserver.wait()
        time.sleep(0.1)
        self.log_examiner.detect_instance_pids()
        logging.info("STARTING SERVICE - DONE")

    def stop_service(self):
        logging.info("STOPPING SERVICE")
        stopserver = psutil.Popen(['service', 'arangodb3', 'stop'])
        logging.info("waiting for eof")
        stopserver.wait()
        while self.check_service_up():
            time.sleep(1)
        logging.info("STOPPING SERVICE - DONE")

    def upgrade_package(self):
        raise Exception("TODO!")

    def install_package(self):
        self.cfg.logDir = Path('/var/log/arangodb3')
        self.cfg.dbdir = Path('/var/lib/arangodb3')
        self.cfg.appdir = Path('/var/lib/arangodb3-apps')
        self.cfg.cfgdir = Path('/etc/arangodb3')
        self.cfg.all_instances = {
            'single': {
                'logfile':
                self.cfg.installPrefix / self.cfg.logDir / 'arangod.log'
            }
        }
        self.log_examiner = ArangodLogExaminer(self.cfg)
        logging.info("installing Arangodb RPM package")
        package = self.cfg.package_dir / self.server_package
        if not package.is_file():
            logging.info("package doesn't exist: %s", str(package))
            raise Exception("failed to find package")

        logging.info("-"*80)
        server_install = pexpect.spawnu('rpm ' + '-i ' + str(package))
        reply = None
        try:
            server_install.expect('the current password is')
            print(server_install.before)
            server_install.expect(pexpect.EOF, timeout=30)
            reply = server_install.before
            print(reply)
            logging.info("-"*80)
        except pexpect.exceptions.EOF:
            logging.info("X" * 80)
            print(server_install.before)
            logging.info("X" * 80)
            logging.info("Installation failed!")
            sys.exit(1)
        start = reply.find("'")
        end = reply.find("'", start + 1)
        self.cfg.passvoid = reply[start + 1: end]

        self.start_service()

        self.log_examiner.detect_instance_pids()

        pwcheckarangosh = ArangoshExecutor(self.cfg)
        if not pwcheckarangosh.js_version_check():
            logging.info(
                "Version Check failed -"
                "probably setting the default random password didn't work! %s",
                self.cfg.passvoid)

        self.stop_service()

        self.cfg.passvoid = "sanoetuh"   # TODO
        with pexpect.spawnu('/usr/sbin/arango-secure-installation') as etpw:
            result = None
            try:
                ask_for_pass=[
                    'Please enter a new password for the ArangoDB root user:',
                    'Please enter password for root user:',
                ]

                result = etpw.expect(ask_for_pass)
                if result == None:
                    raise RuntimeError("Not asked for password")

                etpw.sendline(self.cfg.passvoid)
                result = etpw.expect('Repeat password:')
                if reult == None:
                    raise RuntimeError("Not asked to repeat the password")
                logging.info("@@@@@@@@@@@@@@@@@@@@ password should be set to: " + self.cfg.password)
                etpw.sendline(self.cfg.passvoid)

                logging.info("expecting eof")
                logging.info("@@@@@@@@@@@@@@@@@@@@ password should be set to: " + self.cfg.password)
                result = etpw.expect(pexpect.EOF)

                logging.info("@@@@@@@@@@@@@@@@@@@@ password should be set to: " + self.cfg.password)

            #except pexpect.exceptions.EOF:
            except Exception as e:
                logging.error("setting our password failed!")
                logging.error("X" * 80)
                print("XO" * 80)
                logging.error(repr(self.cfg))
                logging.error("X" * 80)
                logging.error("result: " + str(result))
                logging.error("X" * 80)
                print(etpw.before)
                logging.error("X" * 80)

                sys.exit(1)
        self.start_service()
        self.log_examiner.detect_instance_pids()

    def un_install_package(self):
        uninstall = psutil.Popen(['rpm', '-e', 'arangodb3' +
                                  ('e' if self.cfg.enterprise else '')])
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
