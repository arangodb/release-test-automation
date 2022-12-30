#!/usr/bin/env python3
"""License manager test suite(upgrade)"""
import platform

from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from license_manager_tests.upgrade.afo import LicenseManagerAfoUpgradeTestSuite
from license_manager_tests.upgrade.cluster import LicenseManagerClusterUpgradeTestSuite
from license_manager_tests.upgrade.dc2dc import LicenseManagerDc2DcUpgradeTestSuite
from license_manager_tests.upgrade.leader_follower import LicenseManagerLeaderFollowerUpgradeTestSuite

IS_WINDOWS = platform.win32_ver()[0] != ""


class UpgradeLicenseManagerTestSuite(LicenseManagerBaseTestSuite):
    """License manager test suite: Upgrade"""

    child_test_suites = [
        LicenseManagerLeaderFollowerUpgradeTestSuite,
        LicenseManagerClusterUpgradeTestSuite,
        LicenseManagerAfoUpgradeTestSuite,
    ]

    if not IS_WINDOWS:
        child_test_suites.append(LicenseManagerDc2DcUpgradeTestSuite)
