"""License manager tests: active failover"""

# pylint: disable=import-error
from license_manager_tests.base.afo_base import LicenseManagerAfoBaseTestSuite
from selenium_ui_test.test_suites.base_test_suite import testcase


class LicenseManagerAfoTestSuite(LicenseManagerAfoBaseTestSuite):
    """License manager tests: active failover"""

    @testcase
    def clean_install_temp_license(self):
        """Check that server gets a 60-minute license after installation on a clean system"""
        self.check_that_license_is_not_expired(50 * 60)
        self.check_not_readonly()

    @testcase
    def goto_read_only_mode_when_license_expired(self):
        """Check that system goes to read-only mode when license is expired"""
        self.expire_license()
        self.check_readonly()
