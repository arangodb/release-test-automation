import platform
import pprint

from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.pages.replication_page import ReplicationPage
from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase

from selenium_ui_test.test_suites.activefailover.after_install_test_suite import (
    ActiveFailoverAfterInstallTestSuite,
)


class ActiveFailoverJamStepOneSuite(BaseTestSuite):
    WINVER = platform.win32_ver()

    @testcase
    def jam_step_1(self):
        """check for one set of instances to go away"""
        NavigationBarPage(self.webdriver).navbar_goto("replication")
        replication_page = ReplicationPage(self.webdriver)
        replication_table = replication_page.get_replication_screen(True)
        print(replication_table)
        # head and one follower should be there:
        self.ui_assert(
            len(replication_table["follower_table"]) == 2,
            "UI-Test:\nexpect 2 followers in:\n %s" % pprint.pformat(replication_table),
        )

    @testcase
    def check_follower_count(self):
        """check the integrity of the system"""
        ActiveFailoverAfterInstallTestSuite.check_old(self, expect_follower_count=1)
