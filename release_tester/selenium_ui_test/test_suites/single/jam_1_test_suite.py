#!/usr/bin/env python3
""" jamming leader follower testsuite """

from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase


class SingleJamStepOneSuite(BaseSeleniumTestSuite):
    """ jamming leader follower testsuite """
    @testcase
    def test(self):
        """check for one set of instances to go away"""
        self.go_to_index_page()
