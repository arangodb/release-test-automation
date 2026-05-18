"""Managed license tests: single server"""


from license_manager_tests.base.single_server_base import LicenseManagerSingleServerBaseTestSuite
from license_manager_tests.base.managed_license_base import ManagedLicenseBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import testcase, run_before_each_testcase, disable
from test_suites_core.cli_test_suite import CliTestSuiteParameters
from license_manager_tests.helpers.license_helper import (
    LicenseHelper,
    DEFAULT_CLIENT_ID,
    DEFAULT_CLIENT_SECRET,
    MAX_ACTIVE_DEPLOYMENTS,
)


class ManagedLicenseSingleServerTestSuite(LicenseManagerSingleServerBaseTestSuite, ManagedLicenseBaseTestSuite):
    """Managed license tests: single server"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.suite_name = "Managed license test suite: Clean install"
        self.first_test = True

    @run_before_each_testcase
    @step
    def setup_single_server(self):
        """instantiate LicenseHelper and recreate deployment if needed"""
        if not self.first_test:  # we only want to recreate a deployment for 2nd and subsequent tests
            self.recreate_deployment()
        self.first_test = False
        self.lh = LicenseHelper(self.starter, self.lm_tests_dir)

    @testcase("1. Attempt to generate a license key with incorrect client id and secret key - Single server")
    def test_negative_generate_and_apply_license(self):
        """attempt to generate a license key with incorrect client id and secret key"""
        with step("generate a new license key with operator platform tool"):
            self.lh.generate_license_key(client_id=DEFAULT_CLIENT_ID, client_secret=DEFAULT_CLIENT_SECRET)
        license_key_file_content = self.lh.get_license_key_file_content()
        self.lh.apply_license()
        result = self.lh.get_license_data()["json"]
        assert all([s in license_key_file_content for s in ["Error", "401", "unauthorized"]])
        assert not {"license", "grant"}.issubset(result.keys())
        assert "diskUsage" in result

    @testcase("2. Attempt to activate a deployment with incorrect client id and secret key - Single server")
    def test_negative_activate_deployment(self):
        """attempt to activate a deployment with incorrect client id and secret key"""
        with step("use operator platform tool to activate deployment"):
            command_output = self.lh.activate_deployment(
                client_id=DEFAULT_CLIENT_ID, client_secret=DEFAULT_CLIENT_SECRET
            )
        result = self.lh.get_license_data()["json"]
        assert all([s in command_output for s in ["Error", "401", "unauthorized"]])
        assert not {"license", "grant"}.issubset(result.keys())
        assert "diskUsage" in result

    @testcase("3. Generate a license key with operator platform tool and apply the license - Single server")
    def test_generate_and_apply_license(self):
        """generate a new license key with operator platform tool and apply the license"""
        with step("generate a new license key with operator platform tool"):
            self.lh.generate_license_key()
        license_key_file_content = self.lh.get_license_key_file_content()
        if not MAX_ACTIVE_DEPLOYMENTS in license_key_file_content:  # skip verifications if deployments limit is reached
            self.lh.apply_license()
            result = self.lh.get_license_data()["json"]
            assert "license" in result
            assert {"licenseId", "deploymentId"}.issubset(result["grant"].keys())
            assert result["grant"]["managed"]

    @testcase("4. Use operator platform tool to activate deployment - Single server")
    def test_activate_deployment(self):
        """use operator platform tool to activate deployment"""
        with step("use operator platform tool to activate deployment"):
            command_output = self.lh.activate_deployment()
        if not MAX_ACTIVE_DEPLOYMENTS in command_output:  # skip verifications if deployments limit is reached
            result = self.lh.get_license_data()["json"]
            assert "license" in result
            assert {"licenseId", "deploymentId"}.issubset(result["grant"].keys())
            assert result["grant"]["managed"]
