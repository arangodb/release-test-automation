#!/usr/bin/env python3
""" license manager test suites entrypoint """
from license_manager_tests.afo import LicenseManagerAfoTestSuite
from license_manager_tests.cluster import LicenseManagerClusterTestSuite
from license_manager_tests.dc2dc import LicenseManagerDc2DcTestSuite
from license_manager_tests.leader_follower import LicenseManagerLeaderFollowerTestSuite
from license_manager_tests.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from license_manager_tests.single_server import LicenseManagerSingleServerTestSuite
from reporting.reporting_utils import step


class MainLicenseManagerTestSuite(LicenseManagerBaseTestSuite):
    """testsuites entrypoint"""

    def __init__(
        self,
        new_version,
        installer_base_config,
    ):
        super().__init__(
            new_version,
            installer_base_config,
            child_classes=[
                LicenseManagerSingleServerTestSuite,
                LicenseManagerLeaderFollowerTestSuite,
                LicenseManagerAfoTestSuite,
                LicenseManagerClusterTestSuite,
                LicenseManagerDc2DcTestSuite,
            ],
        )

    @step
    def tear_down_test_suite(self):
        """clean up the system after running tests"""
        self.installer.un_install_server_package()

    @step
    def setup_test_suite(self):
        """clean up the system before running tests"""
        self.installer.install_server_package()
        self.installer.stop_service()