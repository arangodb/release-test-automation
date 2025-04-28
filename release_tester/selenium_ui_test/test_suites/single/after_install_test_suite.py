#!/usr/bin/python3
""" test the single server right after the installation"""
from test_suites_core.base_test_suite import testcase
from selenium_ui_test.test_suites.base_classes.after_install_test_suite import AfterInstallTestSuite


class SingleAfterInstallTestSuite(AfterInstallTestSuite):
    """test cases to check the integrity of the old system before the install (Single)"""

    @testcase
    def test(self):
        """check the integrity of the old system after install (single)"""
