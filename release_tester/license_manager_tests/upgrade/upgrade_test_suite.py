#!/usr/bin/env python3
"""License manager test suite(upgrade)"""
import platform

from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite, \
    EXTERNAL_HELPERS_LOADED
from license_manager_tests.upgrade.afo import LicenseManagerAfoUpgradeTestSuite
from license_manager_tests.upgrade.cluster import LicenseManagerClusterUpgradeTestSuite
from license_manager_tests.upgrade.dc2dc import LicenseManagerDc2DcUpgradeTestSuite
from license_manager_tests.upgrade.leader_follower import LicenseManagerLeaderFollowerUpgradeTestSuite
from license_manager_tests.upgrade.single_server import LicenseManagerSingleServerUpgradeTestSuite
from test_suites_core.base_test_suite import disable_if_false

IS_WINDOWS = platform.win32_ver()[0] != ""


@disable_if_false(EXTERNAL_HELPERS_LOADED, "External helpers not found. License manager tests will not run.")
class UpgradeLicenseManagerTestSuite(LicenseManagerBaseTestSuite):
    """License manager test suite: Upgrade"""

    child_test_suites = [
        LicenseManagerSingleServerUpgradeTestSuite,
        LicenseManagerLeaderFollowerUpgradeTestSuite,
        LicenseManagerClusterUpgradeTestSuite,
        LicenseManagerAfoUpgradeTestSuite,
        LicenseManagerDc2DcUpgradeTestSuite,
    ]
