#!/usr/bin/env python3
""" support page testsuite """
from test_suites_core.base_test_suite import testcase
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from selenium_ui_test.pages.support_page import SupportPage


class SupportTestSuite(BaseSeleniumTestSuite):
    """ support page testsuite """
    @testcase
    def test_support(self):
        """testing support page"""
        self.tprint("---------Checking Support page started--------- \n")
        # login = LoginPage(self.webdriver, self.cfg, self.video_start_time)
        # login.login('root', self.root_passvoid)

        # creating multiple support page obj
        support = SupportPage(self.webdriver, self.cfg, self.video_start_time)

        self.tprint("Selecting Support Page \n")
        support.select_support_page()

        self.tprint("Selecting documentation tab \n")
        support.select_documentation_support()
        self.tprint("Checking all arangodb manual link\n")
        if support.version_is_older_than("3.11.99"):
            support.manual_link()
        self.tprint("Checking all AQL Query Language link\n")
        support.aql_query_language_link()
        if support.version_is_newer_than("3.11.99") and self.is_enterprise:
            self.tprint("Checking all Fox Framework link \n")
            support.fox_framework_link()
            self.tprint("Checking all Drivers and Integration links\n")
            support.driver_and_integration_link()
            self.tprint("Checking Community Support tab \n")
            support.community_support_link()
        # self.tprint("Checking Rest API tab \n")
        # # support.rest_api()

        support.print_combined_performance_results()
        del support
        self.tprint("---------Checking Support page completed--------- \n")
