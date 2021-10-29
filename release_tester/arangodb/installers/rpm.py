#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import time
import os
import sys
import shutil
import logging
from pathlib import Path

from reporting.reporting_utils import step
import pexpect
import psutil
import semver
from arangodb.sh import ArangoshExecutor
from arangodb.installers.linux import InstallerLinux
from tools.asciiprint import ascii_print, print_progress as progress

import tools.loghelper as lh


class InstallerRPM(InstallerLinux):
    """install .rpm's on RedHat, CentOS, Rocky Linux or SuSe systems"""

    def __init__(self, cfg):
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.installer_type = "RPM"

        cfg.install_prefix = Path("/")
        cfg.bin_dir = cfg.install_prefix / "usr" / "bin"
        cfg.sbin_dir = cfg.install_prefix / "usr" / "sbin"
        cfg.real_bin_dir = cfg.bin_dir
        cfg.real_sbin_dir = cfg.sbin_dir
        cfg.localhost = "localhost"

        cfg.log_dir = Path("/var/log/arangodb3")
        cfg.dbdir = Path("/var/lib/arangodb3")
        cfg.appdir = Path("/var/lib/arangodb3-apps")
        cfg.cfgdir = Path("/etc/arangodb3")
        super().__init__(cfg)

    def calculate_package_names(self):
        enterprise = "e" if self.cfg.enterprise else ""
        architecture = "x86_64"

        prerelease = self.cfg.semver.prerelease
        semdict = dict(self.cfg.semver.to_dict())
        if prerelease is None or prerelease == "":
            semdict["prerelease"] = ""
        elif prerelease == "nightly":
            semdict["build"] = "0.2"
            self.cfg.semver = semver.VersionInfo.parse("{major}.{minor}.{patch}+{build}".format(**semdict))
            semdict = dict(self.cfg.semver.to_dict())
            semdict["prerelease"] = ""
        elif prerelease.startswith("beta"):
            semdict["prerelease"] = "." + semdict["prerelease"].replace(".", "")
            semdict["build"] = "0.201"
        elif prerelease.startswith("rc"):
            # remove dots, but prepend one:
            semdict["prerelease"] = "." + semdict["prerelease"].replace(".", "")
            semdict["build"] = "0.501"
        elif len(prerelease) > 0:
            # remove dots, but prepend one:
            semdict["prerelease"] = "." + semdict["prerelease"].replace(".", "")

        if not semdict["build"]:
            semdict["build"] = "1.0"

        package_version = "{build}{prerelease}".format(**semdict)

        version = "{major}.{minor}.{patch}".format(**semdict)

        desc = {
            "ep": enterprise,
            "cfg": version,
            "ver": package_version,
            "arch": architecture,
        }

        self.server_package = "arangodb3{ep}-{cfg}-{ver}.{arch}.rpm".format(**desc)
        self.client_package = "arangodb3{ep}-client-{cfg}-{ver}.{arch}.rpm".format(**desc)
        self.debug_package = "arangodb3{ep}-debuginfo-{cfg}-{ver}.{arch}.rpm".format(**desc)

    @step
    def start_service(self):
        assert self.instance

        logging.info("starting service")
        cmd = ["service", "arangodb3", "start"]
        lh.log_cmd(cmd)
        startserver = psutil.Popen(cmd)
        logging.info("waiting for eof of start service")
        startserver.wait()
        time.sleep(0.1)
        self.instance.detect_pid(1)  # should be owned by init

    @step
    def stop_service(self):
        logging.info("stopping service")
        cmd = ["service", "arangodb3", "stop"]
        lh.log_cmd(cmd)
        stopserver = psutil.Popen(cmd)
        logging.info("waiting for eof")
        stopserver.wait()
        while self.check_service_up():
            time.sleep(1)

    @step
    def upgrade_package(self, old_installer):
        logging.info("upgrading Arangodb rpm package")

        self.cfg.passvoid = "RPM_passvoid_%d" % os.getpid()
        self.cfg.log_dir = Path("/var/log/arangodb3")
        self.cfg.dbdir = Path("/var/lib/arangodb3")
        self.cfg.appdir = Path("/var/lib/arangodb3-apps")
        self.cfg.cfgdir = Path("/etc/arangodb3")

        self.set_system_instance()

        # https://access.redhat.com/solutions/1189
        cmd = "rpm --upgrade " + str(self.cfg.package_dir / self.server_package)
        lh.log_cmd(cmd)
        server_upgrade = pexpect.spawnu(cmd)

        try:
            server_upgrade.expect(
                "First Steps with ArangoDB:|server "
                "will now shut down due to upgrade,"
                "database initialization or admin restoration."
            )
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

    @step
    def install_server_package_impl(self):
        # pylint: disable=too-many-statements
        self.cfg.log_dir = Path("/var/log/arangodb3")
        self.cfg.dbdir = Path("/var/lib/arangodb3")
        self.cfg.appdir = Path("/var/lib/arangodb3-apps")
        self.cfg.cfgdir = Path("/etc/arangodb3")
        self.set_system_instance()
        logging.info("installing Arangodb RPM package")
        package = self.cfg.package_dir / self.server_package
        if not package.is_file():
            logging.info("package doesn't exist: %s", str(package))
            raise Exception("failed to find package")

        cmd = "rpm " + "-i " + str(package)
        lh.log_cmd(cmd)
        server_install = pexpect.spawnu(cmd)
        reply = None

        try:
            server_install.expect("the current password is")
            ascii_print(server_install.before)
            server_install.expect(pexpect.EOF, timeout=60)
            reply = server_install.before
            ascii_print(reply)
        except pexpect.exceptions.EOF:
            ascii_print(server_install.before)
            logging.info("Installation failed!")
            sys.exit(1)

        while server_install.isalive():
            progress(".")
            if server_install.exitstatus != 0:
                raise Exception("server installation " "didn't finish successfully!")

        start = reply.find("'")
        end = reply.find("'", start + 1)
        self.cfg.passvoid = reply[start + 1 : end]

        self.start_service()
        self.instance.detect_pid(1)  # should be owned by init

        pwcheckarangosh = ArangoshExecutor(self.cfg, self.instance)
        if not pwcheckarangosh.js_version_check():
            logging.error(
                "Version Check failed -" "probably setting the default random password didn't work! %s",
                self.cfg.passvoid,
            )

        # should we wait for user here? or mark the error in a special way

        self.stop_service()

        self.cfg.passvoid = "RPM_passvoid_%d" % os.getpid()
        lh.log_cmd("/usr/sbin/arango-secure-installation")
        with pexpect.spawnu("/usr/sbin/arango-secure-installation") as etpw:
            result = None
            try:
                ask_for_pass = [
                    "Please enter a new password for the ArangoDB root user:",
                    "Please enter password for root user:",
                ]

                result = etpw.expect(ask_for_pass)
                if result is None:
                    raise RuntimeError("Not asked for password")

                etpw.sendline(self.cfg.passvoid)
                result = etpw.expect("Repeat password: ")
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

            # except pexpect.exceptions.EOF:
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
        self.instance.detect_pid(1)  # should be owned by init

    @step
    def un_install_server_package_impl(self):
        self.stop_service()
        cmd = ["rpm", "-e", "arangodb3" + ("e" if self.cfg.enterprise else "")]
        lh.log_cmd(cmd)
        uninstall = psutil.Popen(cmd)
        uninstall.wait()

    @step
    def install_rpm_package(self, package: str):
        """installing rpm package"""
        print("installing rpm package: %s" % package)
        cmd = "rpm -i " + package
        lh.log_cmd(cmd)
        install = pexpect.spawnu(cmd)
        try:
            logging.info("waiting for the installation to finish")
            install.expect(pexpect.EOF, timeout=90)
            output = install.before
            install.wait()
        except pexpect.exceptions.TIMEOUT:
            logging.info("TIMEOUT!")
            install.close(force=True)
            output = install.before
            raise Exception("Installation of the package {} didn't finish within 90 seconds! Output:\n{}".format(str(package), output))
        if install.exitstatus != 0:
            install.close(force=True)
            raise Exception("Installation of the package {} didn't finish successfully! Output:\n{}".format(str(package), output))
        else:
            logging.info(str(self.debug_package) + " Installation successfull")

    @step
    def install_debug_package_impl(self):
        """installing debug package"""
        self.install_rpm_package(str(self.cfg.package_dir / self.debug_package))
        self.cfg.debug_package_is_installed = True

    @step
    def un_install_package(self, package_name: str):
        """Uninstall package"""
        print("uninstalling rpm package \"%s\"" % package_name)
        uninstall = pexpect.spawnu(
            "rpm -e " + package_name
        )
        try:
            uninstall.expect(pexpect.EOF, timeout=30)
            ascii_print(uninstall.before)
        except pexpect.exceptions.EOF:
            ascii_print(uninstall.before)
            sys.exit(1)

        while uninstall.isalive():
            progress(".")
            if uninstall.exitstatus != 0:
                uninstall.close(force=True)
                ascii_print(uninstall.before)
                raise Exception("Uninstallation of packages %s failed. " % package_name)

    @step
    def install_client_package_impl(self):
        """installing client package"""
        self.install_rpm_package(str(self.cfg.package_dir / self.client_package))
        self.cfg.client_package_is_installed = True

    def un_install_client_package_impl(self):
        """Uninstall client package"""
        print("uninstalling rpm client package")
        package_name = "arangodb3" + ("e-client.x86_64" if self.cfg.enterprise else "-client.x86_64")
        self.un_install_package(package_name)

    def un_install_debug_package_impl(self):
        """Uninstall debug package"""
        print("uninstalling rpm debug package")
        package_name = "arangodb3" + ("e-debuginfo.x86_64" if self.cfg.enterprise else "-debuginfo.x86_64")
        self.un_install_package(package_name)

    @step
    def cleanup_system(self):
        print("attempting system directory cleanup after RPM")
        if self.cfg.log_dir.exists():
            print("cleaning upg %s " % str(self.cfg.log_dir))
            shutil.rmtree(self.cfg.log_dir)
        else:
            print("log directory not known")

        if self.cfg.dbdir.exists():
            print("cleaning upg %s " % str(self.cfg.dbdir))
            shutil.rmtree(self.cfg.dbdir)
        else:
            print("database directory not known")

        if self.cfg.appdir.exists():
            print("cleaning up %s " % str(self.cfg.appdir))
            shutil.rmtree(self.cfg.appdir)
        else:
            print("app directory not known")

        if self.cfg.cfgdir.exists():
            print("cleaning upg %s " % str(self.cfg.cfgdir))
            shutil.rmtree(self.cfg.cfgdir)
        else:
            print("config directory not known")
