#!/usr/bin/env python3
""" jamming leader follower testsuite """
from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase

from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.pages.replication_page import ReplicationPage


class LeaderFollowerJamStepOneSuite(BaseTestSuite):
    """ jamming leader follower testsuite """
    @testcase
    def test(self):
        """check for one set of instances to go away"""
        self.go_to_index_page()
        NavigationBarPage(self.webdriver).navbar_goto("replication")
        replication_page = ReplicationPage(self.webdriver)
        replication_table = replication_page.get_replication_screen(True)
        print(replication_table)
        # head and one follower should be there:
        self.ui_assert(len(replication_table["follower_table"]) == 2, "UI-Test: expected to have 1 follower!")
        # TODO self.check_full_ui(cfg)
