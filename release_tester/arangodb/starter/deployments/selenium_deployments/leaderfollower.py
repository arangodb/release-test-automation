#!/usr/bin/env python3
""" test the UI of a leader follower setup """
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

from selenium_ui_test.test_suites.basic_test_suite import BasicTestSuite
from selenium_ui_test.test_suites.leader_follower.after_install_test_suite import LeaderFollowerAfterInstallTestSuite
from selenium_ui_test.test_suites.leader_follower.jam_1_test_suite import LeaderFollowerJamStepOneSuite


class LeaderFollower(SeleniumRunner):
    """check the leader follower setup and its properties"""

    def __init__(self, webdriver, is_headless: bool, testrun_name: str, ssl: bool, selenium_include_suites: list[str]):
        # pylint: disable=useless-super-delegation
        super().__init__(webdriver, is_headless, testrun_name, ssl, selenium_include_suites)
        self.main_test_suite_list = [BasicTestSuite]
        self.after_install_test_suite_list = [LeaderFollowerAfterInstallTestSuite]
        self.jam_test_suite_list = [LeaderFollowerJamStepOneSuite]

    def test_jam_attempt(self):
        """check the integrity of the old system after jamming setup"""
        self.run_test_suites(self.jam_test_suite_list)
