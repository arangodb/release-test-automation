#!/usr/bin/python3
""" test the leader follower right after the installation"""
import time

from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.pages.replication_page import ReplicationPage
from selenium_ui_test.test_suites.base_test_suite import testcase
from selenium_ui_test.test_suites.base_classes.after_install_test_suite import AfterInstallTestSuite


class LeaderFollowerAfterInstallTestSuite(AfterInstallTestSuite):
    """test cases to check the integrity of the old system before the install (Leader Follower)"""

    @testcase
    def test(self, leader_follower=True):
        """check the integrity of the old system after install (Leader Follower)"""
        count = 0
        replication_table = None
        while True:
            NavigationBarPage(self.webdriver).navbar_goto("replication")
            replication_page = ReplicationPage(self.webdriver)
            replication_table = replication_page.get_replication_screen(leader_follower, 120)
            self.progress(" " + str(replication_table))
            if len(replication_table["follower_table"]) == 2:
                break
            if count % 5 == 0:
                self.webdriver.refresh()
            count += 1
            time.sleep(5)
        # head and one follower should be there:
        self.ui_assert(len(replication_table["follower_table"]) == 2, "UI-Test: expected 1 follower")
