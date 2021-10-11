#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import glob
import logging
import multiprocessing
from pathlib import Path
from pathlib import PureWindowsPath
import shutil
import time
import winreg

from allure_commons._allure import attach
from allure_commons.types import AttachmentType
from mss import mss
import psutil
from reporting.reporting_utils import step
import tools.monkeypatch_psutil
from arangodb.installers.base import InstallerBase


class InstallerW(InstallerBase):
    """install the windows NSIS package"""

    # pylint: disable=R0913 disable=R0902
    def __init__(self, cfg):
        self.server_package = None
        self.client_package = None
        self.service = None
        self.remote_package_dir = "Windows"
        self.installer_type = "NSIS"
        self.backup_dirs_number_before_upgrade = None

        cfg.install_prefix = Path("C:/tmp")
        cfg.log_dir = cfg.install_prefix / "LOG"
        cfg.dbdir = cfg.install_prefix / "DB"
        cfg.appdir = cfg.install_prefix / "APP"
        cfg.install_prefix = cfg.install_prefix / ("PROG" + cfg.version)
        cfg.cfgdir = cfg.install_prefix / "etc/arangodb3"

        cfg.bin_dir = cfg.install_prefix / "usr" / "bin"
        cfg.sbin_dir = cfg.install_prefix / "usr" / "bin"
        cfg.real_bin_dir = cfg.bin_dir
        cfg.real_sbin_dir = cfg.sbin_dir

        super().__init__(cfg)
        self.check_stripped = False
        self.check_symlink = False

    def supports_hot_backup(self):
        """no hot backup support on the wintendo."""
        return False

    def calculate_package_names(self):
        enterprise = "e" if self.cfg.enterprise else ""
        architecture = "win64"
        semdict = dict(self.cfg.semver.to_dict())
        if semdict["prerelease"]:
            semdict["prerelease"] = "-{prerelease}".format(**semdict)
        else:
            semdict["prerelease"] = ""
        version = "{major}.{minor}.{patch}{prerelease}".format(**semdict)
        self.server_package = "ArangoDB3%s-%s_%s.exe" % (
            enterprise,
            version,
            architecture,
        )
        self.client_package = "ArangoDB3%s-client-%s_%s.exe" % (
            enterprise,
            version,
            architecture,
        )
        self.debug_package = None  # TODO

    @step
    def upgrade_package(self, old_installer):
        self.backup_dirs_number_before_upgrade = self.count_backup_dirs()
        self.stop_service()
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
            install.wait(10)
        except psutil.TimeoutExpired as exc:
            print("upgrading timed out, taking screenshot, re-raising!")
            filename = "windows_upgrade_screenshot.png"
            with mss() as sct:
                sct.shot(output=filename)
                attach(
                    filename,
                    name="Screenshot ({fn})".format(fn=filename),
                    attachment_type=AttachmentType.PNG,
                )
            install.kill()
            raise Exception("Upgrade install failed to complete on time") from exc

        self.service = psutil.win_service_get("ArangoDB")
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
    def install_package(self):
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
        install = psutil.Popen(cmd)
        try:
            install.wait(10)
        except psutil.TimeoutExpired as exc:
            print("installing timed out, taking screenshot, re-raising!")
            filename = "windows_upgrade_screenshot.png"
            with mss() as sct:
                sct.shot(output=filename)
                attach(
                    filename,
                    name="Screenshot ({fn})".format(fn=filename),
                    attachment_type=AttachmentType.PNG,
                )
            install.kill()
            raise Exception("Installing failed to complete on time") from exc
        self.service = psutil.win_service_get("ArangoDB")
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

    def get_service(self):
        """get a service handle"""
        if self.service:
            return
        try:
            self.service = psutil.win_service_get("ArangoDB")
        except Exception as exc:
            logging.error("failed to get service! - %s", str(exc))
            return

    def un_install_package_for_upgrade(self):
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
                uninstall.wait(10)
            except psutil.TimeoutExpired as exc:
                print("upgrade uninstall timed out, taking screenshot, re-raising!")
                filename = "windows_upgrade_screenshot.png"
                with mss() as sct:
                    sct.shot(output=filename)
                    attach(
                        filename,
                        name="Screenshot ({fn})".format(fn=filename),
                        attachment_type=AttachmentType.PNG,
                    )
                uninstall.kill()
                raise Exception("upgrade uninstall failed to complete on time") from exc

    @step
    def un_install_package(self):
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
                uninstall.wait(10)
            except psutil.TimeoutExpired as exc:
                print("uninstall timed out, taking screenshot, re-raising!")
                filename = "windows_upgrade_screenshot.png"
                with mss() as sct:
                    sct.shot(output=filename)
                    attach(
                        filename,
                        name="Screenshot ({fn})".format(fn=filename),
                        attachment_type=AttachmentType.PNG,
                    )
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
        try:
            logging.info(psutil.win_service_get("ArangoDB"))
            self.get_service()
            if self.service and self.service.status() != "stopped":
                logging.info("service shouldn't exist anymore!")
        except Exception:
            pass

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
        # TODO: re-enable once https://github.com/giampaolo/psutil/pull/1990 is in a release
        # post psutil 5.8.0
        # self.service.start()
        ret = psutil.Popen(["sc", "start", "ArangoDB"]).wait()
        if ret != 0:
            raise Exception("sc exited non-zero! : %d" % ret)
        while self.service.status() != "running":
            logging.info(self.service.status())
            time.sleep(1)
            if self.service.status() == "stopped":
                raise Exception("arangod service stopped again on its own!" "Configuration / Port problem?")
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
            pass
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
                pass
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
                pass

    def count_backup_dirs(self):
        """get the number of backup paths on disk"""
        regex = (
            str(PureWindowsPath(self.cfg.dbdir))
            + "_[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_[0-9][0-9]_[0-9][0-9]_[0-9][0-9]"
        )
        return len(glob.glob(regex))

    @step
    def check_backup_is_created(self):
        """Check that backup was created after package upgrade"""
        assert (
            self.count_backup_dirs() == self.backup_dirs_number_before_upgrade + 1
        ), "Database files were not backed up during package upgrade"

    def supports_backup(self):
        """Does this installer support automatic backup during minor upgrade?"""
        return True
