#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import platform
from arangodb.sh import ArangoshExecutor
from arangodb.installers.base import InstallerArchive

IS_WINDOWS = platform.win32_ver()[0] != ""


class InstallerSource(InstallerArchive):
    """adjust to arango source directory"""

    def __init__(self, cfg):
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.installer_type = "source directory"
        self.extension = ""
        self.basedir = ""
        self.cfg = cfg
        self.calculate_installation_dirs()
        super().__init__(cfg)
        self.calculate_installation_dirs()
        self.cfg.reset_version(cfg.version)

        self.cfg.localhost = "localhost"

        self.reset_version(self.cfg.version)
        self.check_stripped = False
        self.cfg.have_system_service = False
        self.arangosh = ArangoshExecutor(self.cfg, self.instance)
        self.copy_for_result = False
        self.hot_backup = self.cfg.enterprise

    def calculate_installation_dirs(self):
        # no installing... its there...
        self.cfg.installPrefix = self.cfg.package_dir
        sub_dir = str(self.cfg.version)
        if self.cfg.enterprise:
            sub_dir = "E_" + sub_dir
        test_dir = self.cfg.package_dir / sub_dir
        if not test_dir.exists():
            print("source version sub-directory doesn't exist: " + str(test_dir))
            test_dir = self.cfg.package_dir
        if test_dir.is_symlink():
            test_dir = test_dir.readlink()
        print("identified this source directory: " + str(test_dir))

        self.cfg.bin_dir = test_dir / "build" / "bin"
        if (self.cfg.bin_dir / "RelWithDebInfo").exists():
            self.cfg.bin_dir = self.cfg.bin_dir / "RelWithDebInfo"
        self.cfg.sbin_dir = test_dir / "build" / "bin"
        self.cfg.real_bin_dir = self.cfg.bin_dir
        self.cfg.real_sbin_dir = self.cfg.sbin_dir
        print(self.cfg.bin_dir)
        if not self.cfg.bin_dir.exists():
            raise Exception("unable to locate soure directories and binaries in: " + str(self.cfg.bin_dir))
        self.cfg.log_dir = self.cfg.bin_dir
        self.cfg.dbdir = self.cfg.bin_dir
        self.cfg.appdir = self.cfg.bin_dir
        self.cfg.cfgdir = test_dir / "etc" / "relative"
        js_dir = str(test_dir / "js")
        js_enterprise = []
        js_enterprise_server = []
        if self.cfg.enterprise:
            js_enterprise = ["--javascript.module-directory", str(test_dir / "enterprise" / "js")]
            js_enterprise_server = ["--all.javascript.module-directory", str(test_dir / "enterprise" / "js")]
        self.cfg.default_backup_args = [
            "-c",
            str(self.cfg.cfgdir / "arangobackup.conf"),
        ]
        self.cfg.default_arangosh_args = [
            "-c",
            str(self.cfg.cfgdir / "arangosh.conf"),
            "--javascript.startup-directory",
            js_dir,
        ] + js_enterprise
        self.cfg.default_starter_args = [
            "--server.arangod=" + str(self.cfg.real_sbin_dir / "arangod"),
            "--server.js-dir=" + js_dir,
        ] + js_enterprise_server
        self.cfg.default_imp_args = [
            "-c",
            str(self.cfg.cfgdir / "arangoimport.conf"),
        ]
        self.cfg.default_restore_args = [
            "-c",
            str(self.cfg.cfgdir / "arangoimport.conf"),
        ]

    def supports_hot_backup(self):
        """no hot backup support on the wintendo."""
        if IS_WINDOWS:
            return False
        return super().supports_hot_backup()

    def calculate_package_names(self):
        """nothing to see here"""

    def check_service_up(self):
        """nothing to see here"""

    def start_service(self):
        """nothing to see here"""

    def stop_service(self):
        """nothing to see here"""

    def upgrade_package(self, old_installer):
        """nothing to see here"""

    def install_server_package_impl(self):
        """nothing to see here"""

    def un_install_package(self):
        """nothing to see here"""

    def install_debug_package(self):
        """nothing to see here"""

    def un_install_debug_package(self):
        """nothing to see here"""

    def cleanup_system(self):
        """nothing to see here"""

    def install_client_package_impl(self):
        """nothing to see here"""

    def un_install_client_package_impl(self):
        """nothing to see here"""

    def un_install_server_package_impl(self):
        """nothing to see here"""

    def upgrade_server_package(self, old_installer):
        """nothing to see here"""

    def check_engine_file(self):
        """nothing to see here"""
