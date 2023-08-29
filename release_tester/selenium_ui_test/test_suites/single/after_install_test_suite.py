#!/usr/bin/python3
""" test the leader follower right after the installation"""
import time

from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.pages.replication_page import ReplicationPage
from test_suites_core.base_test_suite import testcase
from selenium_ui_test.test_suites.base_classes.after_install_test_suite import AfterInstallTestSuite


class SingleAfterInstallTestSuite(AfterInstallTestSuite):
    """test cases to check the integrity of the old system before the install (Leader Follower)"""

    @testcase
    def test(self, leader_follower=False):
        """check the integrity of the old system after install (Leader Follower)"""
        count = 0
