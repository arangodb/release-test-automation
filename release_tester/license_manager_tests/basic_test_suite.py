#!/usr/bin/env python3
"""License manager test suite(clean installation)"""
import platform
from copy import deepcopy

from license_manager_tests.afo import LicenseManagerAfoTestSuite
from license_manager_tests.base.license_manager_base_test_suite import (
    LicenseManagerBaseTestSuite,
    EXTERNAL_HELPERS_LOADED,
)
from license_manager_tests.cluster import LicenseManagerClusterTestSuite
from license_manager_tests.dc2dc import LicenseManagerDc2DcTestSuite
from license_manager_tests.leader_follower import LicenseManagerLeaderFollowerTestSuite
from license_manager_tests.single_server import LicenseManagerSingleServerTestSuite
from test_suites_core.base_test_suite import run_before_suite, run_after_suite, disable_if_false
from test_suites_core.cli_test_suite import CliTestSuiteParameters

IS_WINDOWS = platform.win32_ver()[0] != ""


@disable_if_false(EXTERNAL_HELPERS_LOADED, "External helpers not found. License manager tests will not run.")
class BasicLicenseManagerTestSuite(LicenseManagerBaseTestSuite):
    """License manager test suite: Clean installation"""

    child_test_suites = [
        LicenseManagerSingleServerTestSuite,
        LicenseManagerLeaderFollowerTestSuite,
        LicenseManagerAfoTestSuite,
        LicenseManagerClusterTestSuite,
        LicenseManagerDc2DcTestSuite,
    ]

    def __init__(self, params: CliTestSuiteParameters):
        # This test suite is intended to test clean installation.
        # If both old_ version and new_version are set, we must ignore old version.
        local_params = deepcopy(params)
        local_params.old_version = None
        super().__init__(local_params)

    @run_after_suite
    def uninstall_package(self):
        """uninstall package"""
        self.installer.un_install_server_package()
        self.installer.cleanup_system()

    @run_before_suite
    def install_package(self):
        """clean up the system before running the license manager test suites"""
        self.installer.install_server_package()
        self.installer.stop_service()

    def teardown_suite(self):
        """mute parent method"""
