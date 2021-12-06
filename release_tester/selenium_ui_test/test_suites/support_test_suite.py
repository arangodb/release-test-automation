#!/usr/bin/env python3
""" support page testsuite """

from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.support_page import SupportPage


class SupportTestSuite(BaseTestSuite):
    """ support page testsuite """
    @testcase
    def test_support(self):
        """testing support page"""
        print("---------Checking Support page started--------- \n")
        # login = LoginPage(self.webdriver)
        # login.login('root', self.root_passvoid)

        # creating multiple support page obj
        support = SupportPage(self.webdriver)

        print("Selecting Support Page \n")
        support.select_support_page()

        print("Selecting documentation tab \n")
        support.select_documentation_support()
        print("Checking all arangodb manual link\n")
        support.manual_link()
        print("Checking all AQL Query Language link\n")
        support.aql_query_language_link()
        print("Checking all Fox Framework link \n")
        support.fox_framework_link()
        print("Checking all Drivers and Integration links\n")
        support.driver_and_integration_link()
        print("Checking Community Support tab \n")
        support.community_support_link()
        print("Checking Rest API tab \n")
        support.rest_api()

        # logging out from the current user
        # login.logout_button()
        # del login
        del support
        print("---------Checking Support page completed--------- \n")
