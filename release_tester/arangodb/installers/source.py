#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import platform
from arangodb.sh import ArangoshExecutor
from arangodb.installers.base import InstallerBase

IS_WINDOWS = platform.win32_ver()[0] != ""

class InstallerSource(InstallerBase):
    """ adjust to arango source directory """
    def __init__(self, cfg):
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.installer_type = "source directory"
        self.extension = ""
        cfg.reset_version(cfg.version)
        cfg.installPrefix = cfg.package_dir
        sub_dir = str(cfg.version)
        if cfg.enterprise:
            sub_dir = "E_" + sub_dir
        test_dir = cfg.package_dir / sub_dir
        if not test_dir.exists():
            print("source version sub-directory doesn't exist: " + str(test_dir))
            test_dir = cfg.package_dir
        if test_dir.is_symlink():
            test_dir = test_dir.readlink()
        print("identified this source directory: " + str(test_dir))
        # no installing... its there...
        cfg.bin_dir = test_dir / "build" / "bin"
        if (cfg.bin_dir / 'RelWithDebInfo').exists():
            cfg.bin_dir = cfg.bin_dir / 'RelWithDebInfo'
        cfg.sbin_dir = test_dir / "build" / "bin"
        cfg.real_bin_dir = cfg.bin_dir
        cfg.real_sbin_dir = cfg.sbin_dir
        print(cfg.bin_dir)
        if not cfg.bin_dir.exists():
            raise Exception("unable to locate soure directories and binaries in: " + str(cfg.bin_dir))
        cfg.localhost = 'localhost'

        cfg.log_dir = cfg.bin_dir
        cfg.dbdir = cfg.bin_dir
        cfg.appdir = cfg.bin_dir
        cfg.cfgdir = test_dir / 'etc' / 'relative'
        js_dir = str(test_dir / 'js')
        js_enterprise = []
        js_enterprise_server = []
        if cfg.enterprise:
            js_enterprise = [
                '--javascript.module-directory',
                str(test_dir / 'enterprise' / 'js')
                ]
            js_enterprise_server = [
                '--all.javascript.module-directory',
                str(test_dir / 'enterprise' / 'js')
                ]
        cfg.default_backup_args = [
            '-c', str(cfg.cfgdir / 'arangobackup.conf'),
        ]
        cfg.default_arangosh_args = [
            '-c', str(cfg.cfgdir / 'arangosh.conf'),
            '--javascript.startup-directory', js_dir
        ] + js_enterprise
        cfg.default_starter_args = [
            '--server.arangod=' + str(cfg.real_sbin_dir / 'arangod'),
            '--server.js-dir=' + js_dir
        ] + js_enterprise_server
        cfg.default_imp_args = [
            '-c', str(cfg.cfgdir / 'arangoimport.conf'),
        ]
        cfg.default_restore_args = [
            '-c', str(cfg.cfgdir / 'arangoimport.conf'),
        ]
        super().__init__(cfg)
        self.reset_version(cfg.version)
        self.check_stripped = False
        self.cfg.have_system_service = False
        self.arangosh = ArangoshExecutor(self.cfg, self.instance)

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
