#!/usr/bin/python3
"""base class for after installation testuites"""
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite


class AfterInstallTestSuite(BaseSeleniumTestSuite):
    """test cases to check the integrity of the old system before the upgrade"""
