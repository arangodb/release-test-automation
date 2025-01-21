#!/usr/bin/env python3
""" test the UI of a single server setup """
from arangodb.starter.deployments.runner import RunnerProperties
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

from selenium_ui_test.test_suites.basic_test_suite import BasicTestSuite
from selenium_ui_test.test_suites.single.after_install_test_suite import SingleAfterInstallTestSuite
from selenium_ui_test.test_suites.single.jam_1_test_suite import SingleJamStepOneSuite


class Single(SeleniumRunner):
    """check the single setup and its properties"""

    def __init__(self, selenium_args,
                 properties: RunnerProperties,
                 testrun_name: str,
                 ssl: bool,
                 selenium_include_suites: list[str]):
        # pylint: disable=useless-super-delegation disable=too-many-arguments
        super().__init__(selenium_args, properties, testrun_name, ssl, selenium_include_suites)
        self.main_test_suite_list = [BasicTestSuite]
        self.after_install_test_suite_list = [SingleAfterInstallTestSuite]
        self.jam_test_suite_list = [SingleJamStepOneSuite]

    def test_jam_attempt(self):
        """check the integrity of the old system after jamming setup"""
        self.run_test_suites(self.jam_test_suite_list)
