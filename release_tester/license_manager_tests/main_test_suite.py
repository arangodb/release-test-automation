#!/usr/bin/env python3
""" license manager test suites entrypoint """
import platform

from license_manager_tests.afo import LicenseManagerAfoTestSuite
from license_manager_tests.cluster import LicenseManagerClusterTestSuite
from license_manager_tests.leader_follower import LicenseManagerLeaderFollowerTestSuite
from license_manager_tests.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from license_manager_tests.single_server import LicenseManagerSingleServerTestSuite
from selenium_ui_test.test_suites.base_test_suite import run_before_suite, run_after_suite

IS_WINDOWS = platform.win32_ver()[0] != ""


class MainLicenseManagerTestSuite(LicenseManagerBaseTestSuite):
    """testsuites entrypoint"""

    def __init__(
        self,
        new_version,
        installer_base_config,
    ):
        child_classes = [
            LicenseManagerSingleServerTestSuite,
            LicenseManagerLeaderFollowerTestSuite,
            LicenseManagerAfoTestSuite,
            LicenseManagerClusterTestSuite,
        ]
        if not IS_WINDOWS:
            pass
            # child_classes.append(LicenseManagerDc2DcTestSuite)
        super().__init__(
            new_version,
            installer_base_config,
            child_classes=child_classes,
        )

    @run_after_suite
    def uninstall_package(self):
        """uninstall package"""
        self.installer.un_install_server_package()

    @run_before_suite
    def install_package(self):
        """clean up the system before running tests"""
        self.installer.install_server_package()
        self.installer.stop_service()

    def shutdown(self):
        """mute parent method"""