#!/usr/bin/env python3
""" test the UI of a leader follower setup """
import time
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

from selenium_ui_test.test_suites.basic_test_suite import BasicTestSuite
from selenium_ui_test.test_suites.leader_follower.before_upgrade_test_suite import \
    LeaderFollowerBeforeUpgradeTestSuite
from selenium_ui_test.test_suites.leader_follower.jam_1_test_suite import LeaderFollowerJamStepOneSuite


class LeaderFollower(SeleniumRunner):
    """ check the leader follower setup and its properties """
    def __init__(self, webdriver,
                 is_headless: bool,
                 testrun_name: str,
                 ssl: bool):
        # pylint: disable=W0235
        super().__init__(webdriver,
                         is_headless,
                         testrun_name,
                         ssl)
        self.main_test_suite_list = [BasicTestSuite]
        self.before_upgrade_test_suite_list = [LeaderFollowerBeforeUpgradeTestSuite]
        self.jam_step_1_test_suite_list = [LeaderFollowerJamStepOneSuite]

    def upgrade_deployment(self, old_cfg, new_cfg, timeout):
        """ nothing to see here """

