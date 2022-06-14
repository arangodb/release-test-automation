#!/usr/bin/env python3
"""enterprise package conflict checking suite"""
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
from test_suites_core.base_test_suite import (
    testcase,
    disable_if_returns_true_at_runtime,
    disable_for_debian,
    disable_for_windows,
    disable_for_mac,
)


class EnterprisePackageInstallationTestSuite(BasePackageInstallationTestSuite):
    """enterprise package conflict checking suite"""

    # pylint: disable=too-many-arguments disable=line-too-long
    def __init__(self, versions: list, base_config: InstallerBaseConfig):
        super().__init__(versions=versions, base_config=base_config)

    disable_for_debian_bts_684 = disable_for_debian(
        "Package installation/uninstallation tests are temporarily disabled for debian-based linux distros. Waiting for BTS-684."
    )
    disable_for_zip_packages = disable_if_returns_true_at_runtime(
        BasePackageInstallationTestSuite.is_zip, "This test case is not applicable for .zip packages."
    )
    disable_if_client_package_is_not_present = disable_if_returns_true_at_runtime(
        BasePackageInstallationTestSuite.client_package_is_not_present,
        "Test case is skipped because client package is not present for given installer type.",
    )

    # pylint: disable=missing-function-docstring
    def generate_custom_suite_name(self):
        return f"Test package installation/uninstallation. New version: {self.new_version}. Old version: {self.old_version}. Package type: {str(self.new_inst_e.installer_type)}. Enterprise edition."

    @disable_for_debian_bts_684
    @disable_for_windows
    @disable_for_mac
    @disable_for_zip_packages
    @testcase
    def test1(self):
        """Check that new enterprise server package cannot be installed over a community package of previous version"""
        check_if_server_packages_can_be_installed_consequentially(self.old_inst_c, self.new_inst_e, False)

    @disable_for_debian_bts_684
    @disable_for_windows
    @disable_for_mac
    @disable_for_zip_packages
    @testcase
    def test2(self):
        """Check that new enterprise server package cannot be installed over a community package of the same version"""
        check_if_server_packages_can_be_installed_consequentially(self.new_inst_c, self.new_inst_e, False)

    @disable_for_debian_bts_684
    @disable_for_windows
    @disable_for_mac
    @disable_for_zip_packages
    @testcase
    def test3(self):
        """Check that enterprise debug package cannot be installed when community server package of current version is present"""
        check_if_debug_package_can_be_installed_over_server_package(self.new_inst_e, self.new_inst_c, False)

    @disable_for_debian_bts_684
    @disable_for_windows
    @disable_for_mac
    @disable_for_zip_packages
    @testcase
    def test4(self):
        """Check that enterprise debug package cannot be installed when community server package of previous version is present"""
        check_if_debug_package_can_be_installed_over_server_package(self.new_inst_e, self.old_inst_c, False)

    @disable_for_debian_bts_684
    @disable_for_windows
    @disable_for_mac
    @disable_for_zip_packages
    @testcase
    def test5(self):
        """Check that enterprise debug package cannot be installed if server package is not present."""
        check_if_debug_package_can_be_installed(self.new_inst_e, False)

    @disable_for_debian_bts_684
    @disable_for_windows
    @disable_for_mac
    @disable_for_zip_packages
    @testcase
    def test6(self):
        """Check that enterprise debug package can be installed/uninstalled if enterprise server package of the same version is present"""
        check_if_debug_package_can_be_installed_over_server_package(self.new_inst_e, self.new_inst_e, True)

    @disable_for_mac
    @disable_for_zip_packages
    @disable_if_client_package_is_not_present
    @disable_for_windows
    @testcase
    def test7(self):
        """Check that new enterprise client package cannot be installed over an community package of previous version"""
        check_if_client_packages_can_be_installed_consequentially(self.old_inst_c, self.new_inst_e, False)

    @disable_for_mac
    @disable_for_zip_packages
    @disable_for_windows
    @disable_if_client_package_is_not_present
    @testcase
    def test8(self):
        """Check that new enterprise client package cannot be installed over an community package of the same version"""
        check_if_client_packages_can_be_installed_consequentially(self.new_inst_c, self.new_inst_e, False)

    @disable_for_mac
    @disable_for_zip_packages
    @disable_for_windows
    @disable_if_client_package_is_not_present
    @testcase
    def test9(self):
        """Check that new enterprise client package cannot be installed when server package is installed"""
        check_if_client_package_can_be_installed_over_server_package(self.new_inst_e, self.new_inst_e, False)

    @disable_for_mac
    @disable_if_client_package_is_not_present
    @testcase
    def test10(self):
        """Check that enterprise client package can be installed/uninstalled."""
        check_if_client_package_can_be_installed(self.new_inst_e, True)

    @disable_for_debian_bts_684
    @disable_for_windows
    @disable_for_mac
    @disable_for_zip_packages
    @testcase
    def test11(self):
        """Check that new enterprise server package can be installed"""
        check_if_server_package_can_be_installed(self.new_inst_e)

    @disable_for_debian_bts_684
    @disable_for_windows
    @disable_for_mac
    @disable_for_zip_packages
    @testcase
    def test12(self):
        """Check that enterprise server package can be upgraded"""
        check_if_server_packages_can_be_installed_consequentially(self.old_inst_e, self.new_inst_e, True)

    @disable_for_mac
    @disable_if_client_package_is_not_present
    @testcase
    def test13(self):
        """Check that enterprise client package can be upgraded"""
        check_if_client_packages_can_be_installed_consequentially(self.old_inst_e, self.new_inst_e, True)
