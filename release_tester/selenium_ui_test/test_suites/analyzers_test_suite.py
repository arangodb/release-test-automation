#!/usr/bin/env python3
""" analyzer page testsuite 1 """

# from selenium_ui_test.pages.analyzers_page import AnalyzerPage
from selenium_ui_test.test_suites.analyzers_base_test_suite import AnalyzersBaseTestSuite
from test_suites_core.base_test_suite import testcase


class AnalyzersTestSuite(AnalyzersBaseTestSuite):
    """ analyzer page testsuite 1"""
    @testcase
    def test_analyzers(self):
        super().test_analyzers(analyzer_set=1)