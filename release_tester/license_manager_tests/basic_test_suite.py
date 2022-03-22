#!/usr/bin/env python3
"""License manager test suite(clean installation)"""
import platform

from license_manager_tests.afo import LicenseManagerAfoTestSuite
from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from license_manager_tests.cluster import LicenseManagerClusterTestSuite
from license_manager_tests.dc2dc import LicenseManagerDc2DcTestSuite
from license_manager_tests.leader_follower import LicenseManagerLeaderFollowerTestSuite
from license_manager_tests.single_server import LicenseManagerSingleServerTestSuite
from selenium_ui_test.test_suites.base_test_suite import run_before_suite, run_after_suite

IS_WINDOWS = platform.win32_ver()[0] != ""


class BasicLicenseManagerTestSuite(LicenseManagerBaseTestSuite):
    """License manager test suite(clean installation)"""

    def __init__(
            self,
            versions,
            installer_base_config,
    ):
        if len(versions) > 1:
            new_version = versions[1]
        else:
            new_version = versions[0]
        child_classes = [
            LicenseManagerSingleServerTestSuite,
            LicenseManagerLeaderFollowerTestSuite,
            LicenseManagerAfoTestSuite,
            LicenseManagerClusterTestSuite,
        ]
        if not IS_WINDOWS:
            child_classes.append(LicenseManagerDc2DcTestSuite)
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
        """clean up the system before running the license manager test suites"""
        self.installer.install_server_package()
        self.installer.stop_service()

    def teardown_suite(self):
        """mute parent method"""
