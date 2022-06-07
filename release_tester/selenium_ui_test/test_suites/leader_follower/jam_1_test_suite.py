#!/usr/bin/env python3
""" jamming leader follower testsuite """

from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase


from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.pages.replication_page import ReplicationPage


class LeaderFollowerJamStepOneSuite(BaseSeleniumTestSuite):
    """ jamming leader follower testsuite """
    @testcase
    def test(self):
        """check for one set of instances to go away"""
        self.go_to_index_page()
        NavigationBarPage(self.webdriver, self.cfg).navbar_goto("replication")
        replication_page = ReplicationPage(self.webdriver, self.cfg)
        replication_table = replication_page.get_replication_screen(True)
        print(replication_table)
        # head and one follower should be there:
        self.ui_assert(len(replication_table["follower_table"]) == 2, "UI-Test: expected to have 1 follower!")
        # TODO self.check_full_ui(cfg)
