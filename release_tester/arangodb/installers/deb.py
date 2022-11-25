#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import time
import os
import sys
import re
import shutil
import logging
from pathlib import Path

from reporting.reporting_utils import step
import pexpect
import semver
from arangodb.installers.linux import InstallerLinux
from tools.asciiprint import ascii_print, print_progress as progress
import tools.loghelper as lh

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


class InstallerDeb(InstallerLinux):
    """install .deb's on debian or ubuntu hosts"""
    # pylint: disable=too-many-instance-attributes
    def __init__(self, cfg):
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None
        self.installer_type = "DEB"
        self.extension = "deb"
        self.backup_dirs_number_before_upgrade = None

        # Are those required to be stored in the cfg?
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
        package_version = "1"
        architecture = "amd64" if self.machine == "x86_64" else "arm64"

        semdict = dict(self.cfg.semver.to_dict())

        if semdict["prerelease"]:
            if semdict["prerelease"].startswith("nightly"):
                semdict["prerelease"] = "~~{prerelease}".format(**semdict)
            elif semdict["prerelease"].startswith("alpha"):
                semdict["prerelease"] = "~{prerelease}".format(**semdict)
            elif semdict["prerelease"].startswith("beta"):
                semdict["prerelease"] = "~{prerelease}".format(**semdict)
            elif semdict["prerelease"].startswith("rc"):
                semdict["prerelease"] = "~" + semdict["prerelease"].replace("rc", "rc.").replace('..', '.')
            elif re.match(r"\d{1,2}", semdict["prerelease"]):
                semdict["prerelease"] = ".{prerelease}".format(**semdict)
            elif len(semdict["prerelease"]) > 0:
                # semdict["prerelease"] = semdict["prerelease"]
                pass
        else:
            semdict["prerelease"] = ""

        version = "{major}.{minor}.{patch}{prerelease}".format(**semdict)

        desc = {
            "ep": enterprise,
            "cfg": version,
            "ver": package_version,
            "arch": architecture,
        }

        self.server_package = "arangodb3{ep}_{cfg}-{ver}_{arch}.deb".format(**desc)
        self.client_package = "arangodb3{ep}-client_{cfg}-{ver}_{arch}.deb".format(**desc)
        self.debug_package = "arangodb3{ep}-dbg_{cfg}-{ver}_{arch}.deb".format(**desc)

    def start_service(self):
        startserver = pexpect.spawnu("service arangodb3 start")
        logging.debug("waiting for eof")
        startserver.expect(pexpect.EOF, timeout=30)
        while startserver.isalive():
            progress(".")
            if startserver.exitstatus != 0:
                raise Exception("server service start didn't finish successfully!")
        time.sleep(0.1)
        self.instance.detect_pid(1)  # should be owned by init

    def stop_service(self):
        stopserver = pexpect.spawnu("service arangodb3 stop")
        logging.debug("waiting for eof")
        stopserver.expect(pexpect.EOF, timeout=30)
        while stopserver.isalive():
            progress(".")
            if stopserver.exitstatus != 0:
                raise Exception("server service stop didn't finish successfully!")

    @step
    def upgrade_server_package(self, old_installer):
        logging.info("upgrading Arangodb debian package")
        self.backup_dirs_number_before_upgrade = self.count_backup_dirs()
        os.environ["DEBIAN_FRONTEND"] = "readline"
        cmd = "dpkg -i " + str(self.cfg.package_dir / self.server_package)
        lh.log_cmd(cmd)
        server_upgrade = pexpect.spawnu(cmd)
        server_upgrade.logfile = sys.stdout
        while True:
            try:
                i = server_upgrade.expect(
                    [
                        "Upgrading database files",
                        "Database files are up-to-date",
                        "arangod.conf",
                    ],
                    timeout=120,
                )
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
                if i == 2:  # modified arangod.conf...
                    ascii_print(server_upgrade.before)
                    server_upgrade.sendline("Y")
                    # fallthrough - repeat.
            except pexpect.exceptions.EOF as ex:
                logging.info("X" * 80)
                ascii_print(server_upgrade.before)
                logging.info("X" * 80)
                logging.info("[E] Upgrade failed!")
                raise Exception("Upgrade failed!") from ex
        try:
            logging.info("waiting for the upgrade to finish")
            server_upgrade.expect(pexpect.EOF, timeout=30)
            ascii_print(server_upgrade.before)
        except pexpect.exceptions.EOF:
            logging.info("TIMEOUT!")
        self.set_system_instance()
        self.instance.detect_pid(1)  # should be owned by init

    @step
    def install_server_package_impl(self):
        # pylint: disable=too-many-statements
        logging.info("installing Arangodb debian package")
        server_not_started = False
        os.environ["DEBIAN_FRONTEND"] = "readline"
        self.cfg.passvoid = "DEB_passvoid_%d" % os.getpid()
        logging.debug("package dir: {0.cfg.package_dir}- " "server_package: {0.server_package}".format(self))
        cmd = "dpkg -i " + str(self.cfg.package_dir / self.server_package)
        lh.log_cmd(cmd)
        server_install = pexpect.spawnu(cmd)
        server_install.logfile = sys.stdout
        try:
            logging.debug("expect: user1")
            i = server_install.expect(["user:", "arangod.conf"], timeout=120)
            # there are remaints of previous installations.
            # We overwrite existing config files.
            if i == 1:
                server_install.sendline("Y")
                ascii_print(server_install.before)
                server_install.expect("user:")
            ascii_print(server_install.before)
            logging.debug("expect: setting password: " "{0.cfg.passvoid}".format(self))
            server_install.sendline(self.cfg.passvoid)

            logging.debug("expect: user2")
            server_install.expect("user:")
            ascii_print(server_install.before)
            logging.debug("expect: setting password: " "{0.cfg.passvoid}".format(self))
            server_install.sendline(self.cfg.passvoid)

            logging.debug("expect: upgrade behaviour selection")
            server_install.expect(["Automatically upgrade database files", "automatically upgraded"])
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
            server_install.sendline("yes")
        except pexpect.exceptions.EOF as ex:
            lh.line("X")
            ascii_print(server_install.before)
            lh.line("X")
            logging.error("Installation failed!")
            raise Exception("Installation failed!") from ex
        try:
            logging.info("waiting for the installation to finish")
            server_install.expect(pexpect.EOF, timeout=30)
            ascii_print(server_install.before)
            server_not_started = (
                server_install.before.find("not running 'is-active arangodb3.service'") >= 0
                or server_install.before.find("not running 'start arangodb3.service'") >= 0
            )
        except pexpect.exceptions.EOF:
            logging.info("TIMEOUT!")
        while server_install.isalive():
            progress(".")
            if server_install.exitstatus != 0:
                raise Exception("server installation didn't finish successfully!")
        print()
        logging.info("Installation successfull")
        self.set_system_instance()
        if server_not_started:
            logging.info("Environment did not start arango service, doing this now!")
            self.start_service()
        self.instance.detect_pid(1)  # should be owned by init

    @step
    def un_install_server_package_impl(self):
        """ uninstall server package """
        cmd = "dpkg --purge " + "arangodb3" + ("e" if self.cfg.enterprise else "")
        lh.log_cmd(cmd)
        uninstall = pexpect.spawnu(cmd)
        try:
            uninstall.expect(["Purging", "which isn't installed"])
            ascii_print(uninstall.before)
            uninstall.expect(pexpect.EOF)
            ascii_print(uninstall.before)
        except pexpect.exceptions.EOF as ex:
            ascii_print(uninstall.before)
            raise ex
        self.instance.search_for_warnings()

    @step
    def install_debug_package_impl(self):
        """installing debug package"""
        cmd = "dpkg -i " + str(self.cfg.package_dir / self.debug_package)
        lh.log_cmd(cmd)
        os.environ["DEBIAN_FRONTEND"] = "readline"
        debug_install = pexpect.spawnu(cmd)
        try:
            logging.info("waiting for the installation to finish")
            debug_install.expect(pexpect.EOF, timeout=60)
        except pexpect.exceptions.EOF:
            logging.info("TIMEOUT!")
            debug_install.close(force=True)
            ascii_print(debug_install.before)
        print()
        logging.info(str(self.debug_package) + " Installation successfull")

        while debug_install.isalive():
            progress(".")
            if debug_install.exitstatus != 0:
                debug_install.close(force=True)
                ascii_print(debug_install.before)
                raise Exception(str(self.debug_package) + " debug installation didn't finish successfully!")
        return True

    @step
    def un_install_debug_package_impl(self):
        """uninstall debug package"""
        package_name = "arangodb3" + ("e-dbg" if self.cfg.enterprise else "-dbg")
        self.uninstall_package(package_name)

    @step
    def install_client_package_impl(self):
        """install client package"""
        cmd = "dpkg -i " + str(self.cfg.package_dir / self.client_package)
        lh.log_cmd(cmd)
        os.environ["DEBIAN_FRONTEND"] = "readline"
        client_install = pexpect.spawnu(cmd)
        try:
            logging.info("waiting for the installation to finish")
            client_install.expect(pexpect.EOF, timeout=60)
        except pexpect.exceptions.EOF:
            logging.info("TIMEOUT!")
            client_install.close(force=True)
            ascii_print(client_install.before)
        print()
        logging.info(str(self.client_package) + " Installation successful")

        while client_install.isalive():
            progress(".")
        if client_install.exitstatus != 0:
            client_install.close(force=True)
            ascii_print(client_install.before)
            raise Exception(str(self.debug_package) + " client package installation didn't finish successfully!")

    def upgrade_client_package_impl(self):
        self.install_client_package()

    @step
    def un_install_client_package_impl(self):
        """uninstall client package"""
        package_name = "arangodb3" + ("e-client" if self.cfg.enterprise else "-client")
        self.uninstall_package(package_name)

    @step
    def uninstall_package(self, package_name, force=False):
        """uninstall package"""
        os.environ["DEBIAN_FRONTEND"] = "readline"
        force = "--force-depends" if force else ""
        cmd = f"dpkg --purge {force} {package_name}"
        lh.log_cmd(cmd)
        uninstall = pexpect.spawnu(cmd)
        try:
            uninstall.expect(["Removing", "which isn't installed"])
            ascii_print(uninstall.before)
            uninstall.expect(pexpect.EOF, timeout=30)
            ascii_print(uninstall.before)
        except pexpect.exceptions.EOF as ex:
            ascii_print(uninstall.before)
            raise ex

        while uninstall.isalive():
            progress(".")
            if uninstall.exitstatus != 0:
                uninstall.close(force=True)
                ascii_print(uninstall.before)
                raise Exception("Uninstallation of package %s didn't finish successfully!" % package_name)

    def uninstall_everything_impl(self):
        """uninstall all arango packages present in the system(including those installed outside this installer)"""
        for package_name in [
            "arangodb3",
            "arangodb3e",
            "arangodb3-client",
            "arangodb3e-client",
            "arangodb3e-dbg",
            "arangodb3-dbg",
        ]:
            self.uninstall_package(package_name, force=True)

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

    def count_backup_dirs(self):
        """fetch the list of backups available in the system"""
        backups_dir_path = str((self.cfg.dbdir / "..").resolve())
        regex = os.path.basename(self.cfg.dbdir) + r"-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}"
        backups_dir_contents = os.listdir(backups_dir_path)
        backups = [d for d in backups_dir_contents if re.match(regex, d)]
        print("Found %d backup dirs:\n %s" % (len(backups), str(backups)))
        return len(backups)

    @step
    def check_backup_is_created(self):
        """Check that backup was created after package upgrade"""
        assert (
            self.count_backup_dirs() == self.backup_dirs_number_before_upgrade + 1
        ), "Database files were not backed up during package upgrade"

    def supports_backup(self):
        """Does this installer support automatic backup during minor upgrade?"""
        return True
