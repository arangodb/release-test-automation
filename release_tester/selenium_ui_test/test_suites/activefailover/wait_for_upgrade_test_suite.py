#!/usr/bin/env python
"""active failover upgrade testsuite"""

from selenium_ui_test.test_suites.activefailover.active_failover_base_suite import ActiveFailoverBaseTestSuite
from selenium_ui_test.test_suites.base_test_suite import testcase


class ActiveFailoverWaitForUpgradeTestSuite(ActiveFailoverBaseTestSuite):
    """test cases to check the integrity of the old system after the upgrade (Active failover)"""

    @testcase
    def check_version_before_upgrade(self):
        """check for the version to be right"""
        version = (
            self.selenium_runner.new_cfg.version if self.selenium_runner.new_cfg else self.selenium_runner.cfg.version
        )
        self.check_version(version, self.is_enterprise)

    @testcase
    def check_follower_count_testcase(self):
        """check for the follower count"""
        self.check_follower_count()
