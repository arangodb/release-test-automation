#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import time
import sys
import shutil
import logging
from pathlib import Path
import pexpect
import platform
import psutil
from arangodb.sh import ArangoshExecutor
from arangodb.installers.base import InstallerBase
from tools.asciiprint import ascii_print, print_progress as progress

import tools.loghelper as lh

IS_WINDOWS = platform.win32_ver()[0] != ""

class InstallerSource(InstallerBase):
    """ adjust to arango source directory """
    def __init__(self, cfg):
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.installer_type = "source directory"
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
        cfg.bin_dir = cfg.package_dir / "build" / "bin"
        cfg.sbin_dir = cfg.package_dir / "build" / "bin"
        cfg.real_bin_dir = cfg.bin_dir
        cfg.real_sbin_dir = cfg.sbin_dir
        if not cfg.bin_dir.exists():
            raise Exception("unable to locate soure directories and binaries in: " + str(cfg.bin_dir))
        cfg.localhost = 'localhost'

        cfg.log_dir = cfg.bin_dir
        cfg.dbdir = cfg.bin_dir
        cfg.appdir = cfg.bin_dir
        cfg.cfgdir = cfg.package_dir / 'etc' / 'relative'
        js_dir = str(cfg.package_dir / 'js')
        cfg.default_backup_args = [
            '-c', str(cfg.cfgdir / 'arangobackup.conf'),
        ]
        cfg.default_arangosh_args = [
            '-c', str(cfg.cfgdir / 'arangosh.conf'),
            '--javascript.startup-directory', js_dir
        ]
        cfg.default_starter_args = [
            '--server.arangod=' + str(cfg.real_sbin_dir / 'arangod'),
            '--server.js-dir=' + js_dir
        ]

        print('x'*40)
        print(cfg.semver)
        super().__init__(cfg)
        print('x'*40)
        print(self.cfg.semver)
        print(cfg.version)
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

    def upgrade_server_package(self):
        """nothing to see here"""

    def check_engine_file(self):
        """nothing to see here"""
