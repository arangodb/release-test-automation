"""Managed license tests: single server"""

import semver

from license_manager_tests.base.single_server_base import LicenseManagerSingleServerBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import (
    testcase,
    run_before_each_testcase,
    run_before_suite,
)

# pylint: disable=import-error
from test_suites_core.cli_test_suite import CliTestSuiteParameters
from license_manager_tests.helpers.license_helper import LicenseHelper


class ManagedLicenseSingleServerTestSuite(LicenseManagerSingleServerBaseTestSuite):
    """Managed license tests: single server"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.suite_name = "Managed license test suite: Clean install"
        self.first_test_case = True

    def _check_versions_eligible(self):
        """Check that test suite is compatible with ArangoDB versions that are being tested.
        If not, disable test suite.
        """
        if self.new_version is not None and semver.VersionInfo.parse(self.new_version) <= semver.VersionInfo.parse(
            "3.12.8"
        ):
            return False, "This test suite is only applicable to versions above 3.12.8"
        else:
            return True, None

    @run_before_suite
    def download_operator_platform_tool(self):
        """Ensure operator platform tool is available"""
        LicenseHelper.download_operator_platform_tool()

    @run_before_each_testcase
    @step
    def setup_single_server(self):
        """recreate a single server deployment if needed and instantiate LicenseHelper"""
        if not self.first_test_case:  # we only want to recreate a deployment for 2nd and subsequent tests
            self.runner.starter_shutdown()
            self.runner.cleanup()
            self.start_single_server()
        self.first_test_case = False
        self.lh = LicenseHelper(self.starter)

    @testcase
    def test_01_generate_and_apply_license(self):
        """Generate a new license key with operator platform tool and apply the license"""
        self.lh.generate_license_key()
        self.lh.apply_license()
        result = self.lh.get_license_data()
        assert result["json"]["status"] == "good"
        assert result["json"]["grant"]["managed"]

    @testcase
    def test_02_activate_deployment(self):
        """Use operator platform tool to activate deployment"""
        self.lh.activate_deployment()
        result = self.lh.get_license_data()
        assert result["json"]["status"] == "good"
        assert result["json"]["grant"]["managed"]
