#!/usr/bin/env python
"""active failover base testsuite"""
import pprint

from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.pages.replication_page import ReplicationPage
from selenium_ui_test.test_suites.activefailover.active_failover_base_suite import ActiveFailoverBaseTestSuite
from test_suites_core.base_test_suite import testcase


class ActiveFailoverJamStepOneSuite(ActiveFailoverBaseTestSuite):
    """check UI during failover with one node missing"""

    @testcase
    def jam_step_1(self):
        """check for one set of instances to go away"""
        NavigationBarPage(self.webdriver, self.cfg).navbar_goto("replication")
        replication_page = ReplicationPage(self.webdriver, self.cfg)
        replication_table = replication_page.get_replication_screen(True)
        self.print(replication_table)
        # head and one follower should be there:
        self.ui_assert(
            len(replication_table["follower_table"]) == 2,
            "UI-Test:\nexpect 2 followers in:\n %s" % pprint.pformat(replication_table),
        )

    @testcase
    def check_follower_count_testcase(self):
        """check the integrity of the system"""
        self.check_follower_count(expect_follower_count=1)

    @testcase
    def replication_tab_check(self):
        """check that replication tab is reporting correct information"""
        self.check_replication_tab()
