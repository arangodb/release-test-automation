#!/usr/bin/env python3
"""testsuite for community packages"""

from pathlib import Path

from arangodb.installers import InstallerBaseConfig
from package_installation_tests.base_package_installation_test_suite import BasePackageInstallationTestSuite
from package_installation_tests.installation_steps import (
    check_if_server_packages_can_be_installed_consequentially,
    check_if_debug_package_can_be_installed_over_server_package,
    check_if_debug_package_can_be_installed,
    check_if_client_packages_can_be_installed_consequentially,
    check_if_client_package_can_be_installed_over_server_package,
    check_if_client_package_can_be_installed,
    check_if_server_package_can_be_installed,
)
from selenium_ui_test.test_suites.base_test_suite import testcase


class CommunityPackageInstallationTestSuite(BasePackageInstallationTestSuite):
    """testsuite for community packages"""
    # pylint: disable=too-many-arguments disable=line-too-long
    def __init__(
        self,
        old_version,
        new_version,
        alluredir: Path,
        clean_alluredir: bool,
        basecfg: InstallerBaseConfig
    ):
        super().__init__(
            old_version=old_version,
            new_version=new_version,
            alluredir=alluredir,
            clean_alluredir=clean_alluredir,
            basecfg=basecfg
        )
        self.suite_name = f"Test package installation/uninstallation. New version: {new_version}. Old version: {old_version}. Package type: {str(self.new_inst_e.installer_type)}. Community edition."

    @testcase
    def test1(self):
        """Check that new community server package cannot be installed over an enterprise package of previous version"""
        check_if_server_packages_can_be_installed_consequentially(self.old_inst_e, self.new_inst_c, False)

    @testcase
    def test2(self):
        """Check that new community server package cannot be installed over an enterprise package of the same version"""
        check_if_server_packages_can_be_installed_consequentially(self.new_inst_e, self.new_inst_c, False)

    @testcase
    def test3(self):
        """Check that community debug package cannot be installed when enterprise server package of current version is present"""
        check_if_debug_package_can_be_installed_over_server_package(self.new_inst_c, self.new_inst_e, False)

    @testcase
    def test4(self):
        """Check that community debug package cannot be installed when enterprise server package of previous version is present"""
        check_if_debug_package_can_be_installed_over_server_package(self.new_inst_c, self.old_inst_e, False)

    @testcase
    def test5(self):
        """Check that community debug package cannot be installed if server package is not present."""
        check_if_debug_package_can_be_installed(self.new_inst_c, False)

    @testcase
    def test6(self):
        """Check that community debug package can be installed/uninstalled if community server package of the same version is present"""
        check_if_debug_package_can_be_installed_over_server_package(self.new_inst_c, self.new_inst_c, True)

    @testcase
    def test7(self):
        """Check that new community client package cannot be installed over an enterprise package of previous version"""
        check_if_client_packages_can_be_installed_consequentially(self.old_inst_e, self.new_inst_c, False)

    @testcase
    def test8(self):
        """Check that new community client package cannot be installed over an enterprise package of the same version"""
        check_if_client_packages_can_be_installed_consequentially(self.new_inst_e, self.new_inst_c, False)

    @testcase()
    def test9(self):
        """Check that new community client package cannot be installed when server package is installed"""
        check_if_client_package_can_be_installed_over_server_package(self.new_inst_c, self.new_inst_c, False)

    @testcase()
    def test10(self):
        """Check that community client package can be installed/uninstalled."""
        check_if_client_package_can_be_installed(self.new_inst_c, True)

    @testcase
    def test11(self):
        """Check that new community server package can be installed"""
        check_if_server_package_can_be_installed(self.new_inst_c)

    @testcase
    def test12(self):
        """Check that community server package can be upgraded"""
        check_if_server_packages_can_be_installed_consequentially(self.old_inst_c, self.new_inst_c, True)

    @testcase
    def test13(self):
        """Check that community client package can be upgraded"""
        check_if_client_packages_can_be_installed_consequentially(self.old_inst_c, self.new_inst_c, True)
