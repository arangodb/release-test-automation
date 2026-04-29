"""Managed license tests: single server"""


from license_manager_tests.base.single_server_base import LicenseManagerSingleServerBaseTestSuite
from license_manager_tests.base.managed_license_base import ManagedLicenseBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import testcase, run_before_each_testcase

from test_suites_core.cli_test_suite import CliTestSuiteParameters
from license_manager_tests.helpers.license_helper import LicenseHelper, DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET


class ManagedLicenseSingleServerTestSuite(LicenseManagerSingleServerBaseTestSuite, ManagedLicenseBaseTestSuite):
    """Managed license tests: single server"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.suite_name = "Managed license test suite: Clean install"
        self.first_test = True

    @run_before_each_testcase
    @step
    def setup_single_server(self):
        """recreate a single server deployment if needed and instantiate LicenseHelper"""
        if not self.first_test:  # we only want to recreate a deployment for 2nd and subsequent tests
            self.runner.starter_shutdown()
            self.runner.cleanup()
            self.start_single_server()
        self.first_test = False
        self.lh = LicenseHelper(self.starter)

    @testcase
    def test_01_generate_and_apply_license(self):
        """generate a new license key with operator platform tool and apply the license"""
        with step("generate a new license key with operator platform tool"):
            self.lh.generate_license_key()
        self.lh.apply_license()
        result = self.lh.get_license_data()
        assert "license" in result["json"]
        assert "licenseId" in result["json"]["grant"]
        assert "deploymentId" in result["json"]["grant"]
        assert result["json"]["grant"]["managed"]

    @testcase
    def test_02_activate_deployment(self):
        """use operator platform tool to activate deployment"""
        with step("use operator platform tool to activate deployment"):
            self.lh.activate_deployment()
        result = self.lh.get_license_data()
        assert "license" in result["json"]
        assert "licenseId" in result["json"]["grant"]
        assert "deploymentId" in result["json"]["grant"]
        assert result["json"]["grant"]["managed"]

    @testcase
    def test_03_negative_activate_deployment(self):
        """attempt to activate a deployment with incorrect client id and secret key"""
        with step("use operator platform tool to activate deployment"):
            self.lh.activate_deployment(client_id=DEFAULT_CLIENT_ID, client_secret=DEFAULT_CLIENT_SECRET)
        result = self.lh.get_license_data()
        assert "diskUsage" in result["json"]
        assert "license" not in result["json"]
        assert "grant" not in result["json"]
