#!/usr/bin/env python3
""" login testsuite """

from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from selenium_ui_test.test_suites.base_test_suite import testcase
from selenium_ui_test.pages.login_page import LoginPage


class LogInTestSuite(BaseSeleniumTestSuite):
    """ login testsuite """
    @testcase
    def test_login(self):
        """testing login page"""
        print("Starting ", self.webdriver.title, "\n")
        login_page = LoginPage(self.webdriver, self.cfg)
        assert login_page.current_user() == "ROOT", "current user is root?"
        assert login_page.current_database() == "_SYSTEM", "current database is _system?"
        login_page.log_out()

        login_page.login_webif("root", self.root_passvoid)
        login_page.log_out()
        login_page.login_webif("root", self.root_passvoid)
        assert login_page.current_user() == "ROOT", "current user is root?"
        assert login_page.current_database() == "_SYSTEM", "current database is _system?"
