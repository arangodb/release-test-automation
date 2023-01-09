#!/usr/bin/env python3
""" testsuites entrypoint """
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from selenium_ui_test.test_suites.dashboard_test_suite import DashboardTestSuite
from selenium_ui_test.test_suites.database_test_suite import DatabaseTestSuite
from selenium_ui_test.test_suites.login_test_suite import LogInTestSuite
from selenium_ui_test.test_suites.support_test_suite import SupportTestSuite
from selenium_ui_test.test_suites.user_page_test_suite import UserPageTestSuite
from selenium_ui_test.test_suites.collections_test_suite import CollectionsTestSuite
from selenium_ui_test.test_suites.graph_test_suite import GraphTestSuite
from selenium_ui_test.test_suites.query_test_suite import QueryTestSuite
from selenium_ui_test.test_suites.views_test_suite import ViewsTestSuite
from selenium_ui_test.test_suites.analyzers_test_suite import AnalyzersTestSuite
from selenium_ui_test.test_suites.service_test_suit import ServiceTestSuite


class BasicTestSuite(BaseSeleniumTestSuite):
    """testsuites entrypoint"""

    child_test_suites = [
        # UserPageTestSuite,
        # CollectionsTestSuite,
        ViewsTestSuite,
        # GraphTestSuite,
        # QueryTestSuite,
        # AnalyzersTestSuite,
        # DatabaseTestSuite,
        # LogInTestSuite,
        # DashboardTestSuite,
        # SupportTestSuite,
        # ServiceTestSuite,
    ]

    def __init__(self, selenium_runner):
        super().__init__(
            selenium_runner,
        )
