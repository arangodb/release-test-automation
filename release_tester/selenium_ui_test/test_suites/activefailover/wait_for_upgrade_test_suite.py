from selenium_ui_test.test_suites.activefailover.active_failover_base_suite import ActiveFailoverBaseTestSuite
from selenium_ui_test.test_suites.base_test_suite import testcase


class ActiveFailoverWaitForUpgradeTestSuite(ActiveFailoverBaseTestSuite):
    """test cases to check the integrity of the old system after the upgrade (Active failover)"""

    @testcase
    def check_version_before_upgrade(self):
        self.check_version(self.selenium_runner.new_cfg.semver, self.is_enterprise)

    @testcase
    def check_follower_count_testcase(self):
        self.check_follower_count()
