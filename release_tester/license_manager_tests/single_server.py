"""License manager tests: single server"""

from license_manager_tests.base.single_server_base import LicenseManagerSingleServerBaseTestSuite
from test_suites_core.base_test_suite import testcase

# pylint: disable=import-error
from test_suites_core.cli_test_suite import CliTestSuiteParameters


class LicenseManagerSingleServerTestSuite(LicenseManagerSingleServerBaseTestSuite):
    """License manager tests: single server"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.suite_name = "License manager tests: Clean install"

    @testcase
    def clean_install_temp_license(self):
        """Check that server gets a 60-minute license after installation on a clean system"""
        self.check_that_license_is_not_expired(50 * 60)

    @testcase
    def goto_read_only_mode_when_license_expired(self):
        """Check that system goes to read-only mode when license is expired"""
        self.expire_license()
        self.check_readonly()
