#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import logging
import multiprocessing
from pathlib import Path, PureWindowsPath
import shutil
import subprocess
import time
import os
import re

import platform

import semver
from allure_commons._allure import attach
from allure_commons.types import AttachmentType

from arangodb.installers.windows import InstallerWin
from reporting.reporting_utils import step
from tools.killall import get_process_tree

import psutil

# pylint: disable=unused-import
# this will patch psutil for us:
import tools.monkeypatch_psutil

# pylint: disable=import-error, disable=possibly-used-before-assignment
IS_WINDOWS = platform.win32_ver()[0] != ""
if IS_WINDOWS:
    from mss import mss
    import winreg
    import win32api


class InstallerNsis(InstallerWin):
    """install the windows NSIS package"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes
    def __init__(self, cfg):
        self.server_package = None
        self.client_package = None
        self.service = None
        self.remote_package_dir = "Windows"
        self.installer_type = "EXE"
        self.extension = "exe"
        self.backup_dirs_number_before_upgrade = None

        cfg.install_prefix = Path("C:/tmp")
        cfg.log_dir = cfg.install_prefix / "LOG"
        cfg.dbdir = cfg.install_prefix / "DB"
        cfg.appdir = cfg.install_prefix / "APP"
        subdir = "PROG" + cfg.version
        if cfg.semver.prerelease is not None:
            subdir += "_" + cfg.semver.prerelease
        cfg.install_prefix = cfg.install_prefix / subdir
        cfg.cfgdir = cfg.install_prefix / "etc/arangodb3"

        cfg.bin_dir = cfg.install_prefix / "usr" / "bin"
        cfg.sbin_dir = cfg.install_prefix / "usr" / "bin"
        cfg.real_bin_dir = cfg.bin_dir
        cfg.real_sbin_dir = cfg.sbin_dir
        if cfg.semver > semver.VersionInfo.parse("3.9.99"):
            self.arch = "_amd64"
            self.arch = ""
        else:
            self.arch = ""
        self.operating_system = "win64"
        super().__init__(cfg)
        self.check_symlink = False
        self.core_glob = "**/*.dmp"

    def supports_hot_backup(self):
        """no hot backup support on the wintendo."""
        return False

    def _verify_signature(self, programm):
        fulldir = self.cfg.package_dir / programm
        fulldir = fulldir.resolve()
        success_string = b"Successfully verified"
        cmd = ["signtool", "verify", "/pa", str(fulldir)]
        print(cmd)
        with psutil.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            (signtool_str, _) = proc.communicate()
            print(signtool_str)
            if proc.returncode:
                raise Exception("Signtool exited nonzero " + str(cmd) + "\n" + str(signtool_str))
            if signtool_str.find(success_string) < 0:
                raise Exception("Signtool didn't find signature: " + str(signtool_str))

    def calculate_package_names(self):
        enterprise = "e" if self.cfg.enterprise else ""
        semdict = dict(self.cfg.semver.to_dict())
        if semdict["prerelease"]:
            if semdict["prerelease"].startswith("rc"):
                semdict["prerelease"] = "-" + semdict["prerelease"].replace("rc", "rc.").replace("..", ".")
            else:
                semdict["prerelease"] = "-{prerelease}".format(**semdict)
        else:
            semdict["prerelease"] = ""
        version = "{major}.{minor}.{patch}{prerelease}".format(**semdict)

        self.desc = {
            "ep": enterprise,
            "ver": version,
            "os": self.operating_system,
            "arch": self.arch,
            "ext": self.extension,
        }

        self.server_package = "ArangoDB3{ep}-{ver}_{os}{arch}.exe".format(**self.desc)
        if self.cfg.semver >= semver.VersionInfo.parse("3.7.15"):
            self.client_package = "ArangoDB3{ep}-client-{ver}_{os}{arch}.exe".format(**self.desc)
            self.cfg.client_install_prefix = self.cfg.base_test_dir / "arangodb3{ep}-client-{os}_{ver}{arch}".format(
                **self.desc
            )
        self.debug_package = "ArangoDB3{ep}-{ver}.pdb.zip".format(**self.desc)

    @step
    def upgrade_server_package(self, old_installer):
        if not (self.cfg.package_dir / self.server_package).exists():
            raise Exception("Package not found: " + str(self.server_package))
        self._verify_signature(self.server_package)
        self.backup_dirs_number_before_upgrade = self.count_backup_dirs()
        self.stop_service()
        self._verify_signature(self.server_package)
        cmd = [
            str(self.cfg.package_dir / self.server_package),
            "/INSTDIR=" + str(PureWindowsPath(self.cfg.install_prefix)),
            "/DATABASEDIR=" + str(PureWindowsPath(self.cfg.dbdir)),
            "/APPDIR=" + str(PureWindowsPath(self.cfg.appdir)),
            "/PATH=0",
            "/UPGRADE=1",
            "/BACKUP_ON_UPGRADE=1",
            "/S",
            "/INSTALL_SCOPE_ALL=1",
        ]
        logging.info("running windows package installer:")
        logging.info(str(cmd))
        install = psutil.Popen(cmd)
        try:
            install.wait(600)
        except psutil.TimeoutExpired as exc:
            print("upgrading timed out, taking screenshot, re-raising!")
            print("shaking mouse.")
            win32api.SetCursorPos((10, 10))
            time.sleep(1)
            win32api.SetCursorPos((50, 50))
            time.sleep(5)
            print("taking screenshot")
            filename = "windows_upgrade_screenshot.png"
            with mss() as sct:
                sct.shot(output=filename)
                attach.file(
                    filename,
                    name="Screenshot ({fn})".format(fn=filename),
                    attachment_type=AttachmentType.PNG,
                )
            install.kill()
            raise Exception("Upgrade install failed to complete on time") from exc

        self.get_service()
        while not self.check_service_up():
            logging.info("starting...")
            time.sleep(1)
        self.enable_logging()
        self.stop_service()
        # the smaller the wintendo, the longer we shal let it rest,
        # since it needs to look at all these files we
        # just unloaded into it to make sure no harm originates from them.
        time.sleep(60 / multiprocessing.cpu_count())
        self.set_system_instance()
        self.start_service()
        logging.info("Installation successfull")

    @step
    def install_server_package_impl(self):
        if not (self.cfg.package_dir / self.server_package).exists():
            raise Exception("Package not found: " + str(self.server_package))
        self._verify_signature(self.server_package)
        cmd = [
            str(self.cfg.package_dir / self.server_package),
            "/PASSWORD=" + self.cfg.passvoid,
            "/INSTDIR=" + str(PureWindowsPath(self.cfg.install_prefix)),
            "/DATABASEDIR=" + str(PureWindowsPath(self.cfg.dbdir)),
            "/BACKUP_ON_UPGRADE=1",
            "/APPDIR=" + str(PureWindowsPath(self.cfg.appdir)),
            "/PATH=0",
            "/S",
            "/INSTALL_SCOPE_ALL=1",
        ]
        logging.info("running windows package installer:")
        logging.info(str(cmd))
        attach(str(cmd), "Command")
        install = psutil.Popen(cmd)
        try:
            install.wait(600)
        except psutil.TimeoutExpired as exc:
            print("installing timed out, taking screenshot, re-raising!")
            print("shaking mouse.")
            win32api.SetCursorPos((10, 10))
            time.sleep(1)
            win32api.SetCursorPos((50, 50))
            time.sleep(5)
            print("taking screenshot")
            filename = "windows_upgrade_screenshot.png"
            with mss() as sct:
                sct.shot(output=filename)
                attach.file(
                    filename,
                    name="Screenshot ({fn})".format(fn=filename),
                    attachment_type=AttachmentType.PNG,
                )
            install.kill()
            raise Exception("Installing failed to complete on time") from exc
        self.get_service()
        while not self.check_service_up():
            logging.info("starting...")
            time.sleep(1)
        self.enable_logging()
        self.stop_service()
        # the smaller the wintendo, the longer we shal let it rest,
        # since it needs to look at all these files we
        # just unloaded into it to make sure no harm originates from them.
        time.sleep(60 / multiprocessing.cpu_count())
        self.set_system_instance()
        self.start_service()
        logging.info("Installation successfull")

    @step
    def install_client_package_impl(self):
        """Install client package"""
        if not (self.cfg.package_dir / self.server_package).exists():
            raise Exception("Package not found: " + str(self.client_package))
        self._verify_signature(self.client_package)
        cmd = [
            str(self.cfg.package_dir / self.client_package),
            "/INSTDIR=" + str(PureWindowsPath(self.cfg.install_prefix)),
            "/APPDIR=" + str(PureWindowsPath(self.cfg.appdir)),
            "/PATH=0",
            "/S",
            "/INSTALL_SCOPE_ALL=1",
        ]
        logging.info("running windows package installer:")
        logging.info(str(cmd))
        install = psutil.Popen(cmd)
        try:
            install.wait(600)
        except psutil.TimeoutExpired as exc:
            print("installing timed out, taking screenshot, re-raising!")
            print("shaking mouse.")
            win32api.SetCursorPos((10, 10))
            time.sleep(1)
            win32api.SetCursorPos((50, 50))
            time.sleep(5)
            print("taking screenshot")
            filename = "windows_install_client_package.png"
            with mss() as sct:
                sct.shot(output=filename)
                attach.file(
                    filename,
                    name="Screenshot ({fn})".format(fn=filename),
                    attachment_type=AttachmentType.PNG,
                )
            install.kill()
            raise Exception("Installing failed to complete on time") from exc
        logging.info("Installation successfull")

    def get_service(self):
        """get a service handle"""
        if self.service:
            return
        # pylint: disable=broad-except
        try:
            logging.info("getting service")
            self.service = psutil.win_service_get("ArangoDB")
            logging.info("getting service done")
        except Exception as exc:
            logging.error("failed to get service! - %s", str(exc))
            return

    def un_install_server_package_for_upgrade(self):
        """hook to uninstall old package for upgrade"""
        # once we modify it, the uninstaller will leave it there...
        if self.get_arangod_conf().exists():
            self.get_arangod_conf().unlink()
        uninstaller = "Uninstall.exe"
        tmp_uninstaller = Path("c:/tmp") / uninstaller
        uninstaller = self.cfg.install_prefix / uninstaller

        if uninstaller.exists():
            # copy out the uninstaller as the windows facility would do:
            shutil.copyfile(uninstaller, tmp_uninstaller)

            cmd = [
                tmp_uninstaller,
                "/PURGE_DB=0",
                "/S",
                "_?=" + str(PureWindowsPath(self.cfg.install_prefix)),
            ]
            logging.info("running windows package uninstaller")
            logging.info(str(cmd))
            uninstall = psutil.Popen(cmd)
            try:
                uninstall.wait(600)
            except psutil.TimeoutExpired as exc:
                print("upgrade uninstall timed out, taking screenshot, re-raising!")
                print("shaking mouse.")
                win32api.SetCursorPos((10, 10))
                time.sleep(1)
                win32api.SetCursorPos((50, 50))
                time.sleep(5)
                print("taking screenshot")
                filename = "windows_upgrade_screenshot.png"
                with mss() as sct:
                    sct.shot(output=filename)
                    attach.file(
                        filename,
                        name="Screenshot ({fn})".format(fn=filename),
                        attachment_type=AttachmentType.PNG,
                    )
                print(get_process_tree())
                uninstall.kill()
                raise Exception("upgrade uninstall failed to complete on time") from exc

    @step
    def un_install_server_package_impl(self):
        # once we modify it, the uninstaller will leave it there...
        if self.get_arangod_conf().exists():
            self.get_arangod_conf().unlink()
        uninstaller = "Uninstall.exe"
        tmp_uninstaller = Path("c:/tmp") / uninstaller
        uninstaller = self.cfg.install_prefix / uninstaller

        if uninstaller.exists():
            # copy out the uninstaller as the windows facility would do:
            shutil.copyfile(uninstaller, tmp_uninstaller)

            cmd = [
                tmp_uninstaller,
                "/PURGE_DB=1",
                "/S",
                "_?=" + str(PureWindowsPath(self.cfg.install_prefix)),
            ]
            logging.info("running windows package uninstaller")
            logging.info(str(cmd))
            uninstall = psutil.Popen(cmd)
            try:
                uninstall.wait(600)
            except psutil.TimeoutExpired as exc:
                print("uninstall timed out, taking screenshot, re-raising!")
                print("shaking mouse.")
                win32api.SetCursorPos((10, 10))
                time.sleep(1)
                win32api.SetCursorPos((50, 50))
                time.sleep(5)
                print("taking screenshot")
                filename = "windows_upgrade_screenshot.png"
                with mss() as sct:
                    sct.shot(output=filename)
                    attach.file(
                        filename,
                        name="Screenshot ({fn})".format(fn=filename),
                        attachment_type=AttachmentType.PNG,
                    )
                print(get_process_tree())
                uninstall.kill()
                raise Exception("uninstall failed to complete on time") from exc
        if self.cfg.log_dir.exists():
            shutil.rmtree(self.cfg.log_dir)
        if tmp_uninstaller.exists():
            tmp_uninstaller.unlink()
        # the smaller the wintendo, the longer we shal let it rest,
        # since it needs to look at all these files we
        # just unloaded into it to make sure no harm originates from them.
        time.sleep(30 / multiprocessing.cpu_count())
        # pylint: disable=broad-except, disable=unnecessary-pass
        try:
            self.get_service()
            if self.service and self.service.status() != "stopped":
                logging.info("service shouldn't exist anymore!")
        except Exception:
            pass

    @step
    def un_install_client_package_impl(self):
        """Uninstall client package"""
        uninstaller = "Uninstall.exe"
        tmp_uninstaller = Path("c:/tmp") / uninstaller
        uninstaller = self.cfg.install_prefix / uninstaller

        if uninstaller.exists():
            # copy out the uninstaller as the windows facility would do:
            shutil.copyfile(uninstaller, tmp_uninstaller)

            cmd = [
                tmp_uninstaller,
                "/S",
                "_?=" + str(PureWindowsPath(self.cfg.install_prefix)),
            ]
            logging.info("running windows package uninstaller")
            logging.info(str(cmd))
            uninstall = psutil.Popen(cmd)
            try:
                uninstall.wait(600)
            except psutil.TimeoutExpired as exc:
                print("uninstall timed out, taking screenshot, re-raising!")
                print("shaking mouse.")
                win32api.SetCursorPos((10, 10))
                time.sleep(1)
                win32api.SetCursorPos((50, 50))
                time.sleep(5)
                print("taking screenshot")
                filename = "windows_uninstall_client_package_screenshot.png"
                with mss() as sct:
                    sct.shot(output=filename)
                    attach.file(
                        filename,
                        name="Screenshot ({fn})".format(fn=filename),
                        attachment_type=AttachmentType.PNG,
                    )
                print(get_process_tree())
                uninstall.kill()
                raise Exception("uninstall failed to complete on time") from exc
        if self.cfg.log_dir.exists():
            shutil.rmtree(self.cfg.log_dir)
        if tmp_uninstaller.exists():
            tmp_uninstaller.unlink()

    @step
    def uninstall_everything_impl(self):
        """uninstall all arango packages present in the system(including those installed outside this installer)"""
        self.un_install_server_package_impl()
        self.un_install_client_package_impl()

    @step
    def check_service_up(self):
        self.get_service()
        return self.service and self.service.status() == "running"

    @step
    def start_service(self):
        self.get_service()
        if not self.service:
            logging.error("no service registered, not starting")
            return
        self.service.start()
        while self.service.status() != "running":
            logging.info(self.service.status())
            time.sleep(1)
            if self.service.status() == "stopped":
                raise Exception("arangod service stopped again on its own! Configuration / Port problem?")
        # should be owned by init TODO wintendo what do you do here?
        self.instance.detect_pid(1)

    @step
    def stop_service(self):
        self.get_service()
        if not self.service:
            logging.error("no service registered, not stopping")
            return
        if self.service.status() != "stopped":
            self.service.stop()
        while self.service.status() != "stopped":
            logging.info(self.service.status())
            time.sleep(1)

    @step
    def cleanup_system(self):
        # TODO: should this be cleaned by the nsis uninstall in first place?
        if self.cfg.log_dir.exists():
            shutil.rmtree(self.cfg.log_dir)
        if self.cfg.dbdir.exists():
            shutil.rmtree(self.cfg.dbdir)
        if self.cfg.appdir.exists():
            shutil.rmtree(self.cfg.appdir)
        if self.cfg.cfgdir.exists():
            shutil.rmtree(self.cfg.cfgdir)
        try:
            print("force deleting the arangodb service")
            psutil.Popen(["sc", "delete", "arangodb"]).wait()
        except FileNotFoundError:
            print("No service installed.")
        with winreg.OpenKeyEx(
            winreg.HKEY_CURRENT_USER,
            "Software\\Microsoft\\Windows NT\\CurrentVersion\\AppCompatFlags\\Compatibility Assistant\\Store",
            access=winreg.KEY_WRITE,
        ) as k:
            try:
                index = 0
                while True:
                    key, _, _ = winreg.EnumValue(k, index)
                    if key.find("ArangoDB") >= 0:
                        print("deleting v-key: " + key)
                        winreg.DeleteValue(k, key)
                    index = index + 1
            except OSError:
                print("      done")
        with winreg.OpenKeyEx(winreg.HKEY_CURRENT_CONFIG, "Software", access=winreg.KEY_WRITE) as k:
            try:
                index = 0
                while True:
                    key = winreg.EnumKey(k, index)
                    print("key: " + key)
                    if key.find("ArangoDB") >= 0:
                        print("deleting key: " + key)
                        winreg.DeleteKey(k, key)
                    index = index + 1
            except OSError:
                print("      done")

    def count_backup_dirs(self):
        """get the number of backup paths on disk"""
        backups_dir_path = str((self.cfg.dbdir / "..").resolve())
        regex = os.path.basename(self.cfg.dbdir) + r"_\d{4}-\d{1,2}-\d{1,2}_\d{1,2}_\d{1,2}_\d{1,2}"
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
