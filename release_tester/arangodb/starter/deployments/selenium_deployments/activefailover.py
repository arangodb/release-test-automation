#!/usr/bin/env python3
""" test the UI of a active failover setup """
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner
from selenium_ui_test.test_suites.activefailover.before_upgrade_test_suite import \
    ActiveFailoverBeforeUpgradeTestSuite
from selenium_ui_test.test_suites.activefailover.jam_1_test_suite import \
    ActiveFailoverJamStepOneSuite
from selenium_ui_test.test_suites.basic_test_suite import BasicTestSuite


class ActiveFailover(SeleniumRunner):
    """ check the active failover setup and its properties """
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
        self.before_upgrade_test_suite_list = [ActiveFailoverBeforeUpgradeTestSuite]
        self.after_upgrade_test_suite_list = []
        self.jam_step_1_test_suite_list = [ActiveFailoverJamStepOneSuite]
        self.jam_step_2_test_suite_list = []
