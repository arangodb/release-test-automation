"""Managed license tests: cluster"""


from license_manager_tests.base.cluster_base import LicenseManagerClusterBaseTestSuite
from license_manager_tests.base.managed_license_base import ManagedLicenseBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import testcase, run_before_each_testcase
from test_suites_core.cli_test_suite import CliTestSuiteParameters
from license_manager_tests.helpers.license_helper import LicenseHelper, DEFAULT_CLIENT_ID, DEFAULT_CLIENT_SECRET


class ManagedLicenseClusterTestSuite(LicenseManagerClusterBaseTestSuite, ManagedLicenseBaseTestSuite):
    """Managed license tests: cluster"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.suite_name = "Managed license test suite: Clean install"
        self.first_test = True

    @run_before_each_testcase
    @step
    def setup_cluster(self):
        """recreate a cluster deployment if needed and instantiate LicenseHelper"""
        if not self.first_test:  # we only want to recreate a deployment for 2nd and subsequent tests
            self.recreate_deployment()
        self.first_test = False
        self.lh = LicenseHelper(self.starter, self.lm_tests_dir)

    @testcase("1. Attempt to generate a license key with incorrect client id and secret key - Cluster")
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

    @testcase("2. Generate a license key with operator platform tool and apply the license - Cluster")
    def test_generate_and_apply_license(self):
        """generate a new license key with operator platform tool and apply the license"""
        with step("generate a new license key with operator platform tool"):
            self.lh.generate_license_key()
        self.lh.apply_license()
        result = self.lh.get_license_data()["json"]
        assert "license" in result
        assert {"licenseId", "deploymentId"}.issubset(result["grant"].keys())
        assert result["grant"]["managed"]

    @testcase("3. Attempt to activate a deployment with incorrect client id and secret key - Cluster")
    def test_negative_activate_deployment(self):
        """attempt to activate a deployment with incorrect client id and secret key"""
        with step("use operator platform tool to activate deployment"):
            self.lh.activate_deployment(client_id=DEFAULT_CLIENT_ID, client_secret=DEFAULT_CLIENT_SECRET)
        result = self.lh.get_license_data()["json"]
        assert not {"license", "grant"}.issubset(result.keys())
        assert "diskUsage" in result

    @testcase("4. Use operator platform tool to activate deployment - Cluster")
    def test_activate_deployment(self):
        """use operator platform tool to activate deployment"""
        with step("use operator platform tool to activate deployment"):
            self.lh.activate_deployment()
        result = self.lh.get_license_data()["json"]
        assert "license" in result
        assert {"licenseId", "deploymentId"}.issubset(result["grant"].keys())
        assert result["grant"]["managed"]
