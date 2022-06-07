#!/usr/bin/env python3
"""License manager test suite(upgrade)"""
import platform

from license_manager_tests.upgrade.afo import LicenseManagerAfoUpgradeTestSuite
from license_manager_tests.upgrade.cluster import LicenseManagerClusterUpgradeTestSuite
from license_manager_tests.upgrade.dc2dc import LicenseManagerDc2DcUpgradeTestSuite
from license_manager_tests.upgrade.leader_follower import LicenseManagerLeaderFollowerUpgradeTestSuite
from test_suites_core.base_test_suite import BaseTestSuite

IS_WINDOWS = platform.win32_ver()[0] != ""


class UpgradeLicenseManagerTestSuite(BaseTestSuite):
    """License manager test suite(upgrade)"""

    child_test_suites = [
        LicenseManagerLeaderFollowerUpgradeTestSuite,
        LicenseManagerClusterUpgradeTestSuite,
        LicenseManagerAfoUpgradeTestSuite,
    ]

    if not IS_WINDOWS:
        child_test_suites.append(LicenseManagerDc2DcUpgradeTestSuite)

    def __init__(
        self,
        versions,
        installer_base_config,
    ):
        self.new_version = versions[1]
        self.old_version = versions[0]
        self.base_cfg = installer_base_config
        package_type = ".tar.gz" if installer_base_config.zip_package else ".deb/.rpm/NSIS"
        self.suite_name = f"Licence manager test suite: ArangoDB v. {str(self.new_version)} ({package_type})"
        self.auto_generate_parent_test_suite_name = False
        super().__init__()

    def init_child_class(self, child_class):
        """initialise the child class"""
        return child_class(self.old_version, self.new_version, self.base_cfg)
