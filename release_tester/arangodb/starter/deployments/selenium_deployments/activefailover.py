#!/usr/bin/env python3
""" test the UI of a active failover setup """
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner
from selenium_ui_test.test_suites.activefailover.after_install_test_suite import \
    ActiveFailoverAfterInstallTestSuite
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
        self.after_install_test_suite_list = [ActiveFailoverAfterInstallTestSuite]
        self.jam_test_suite_list = [ActiveFailoverJamStepOneSuite]

    def test_jam_attempt(self):
        """ check the integrity of the old system after jamming setup """
        self.run_test_suites(self.jam_test_suite_list)

