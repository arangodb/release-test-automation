from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.analyzersPage import AnalyzerPage

from selenium_ui_test.test_suites.dashboard_test_suite import DashboardTestSuite
from selenium_ui_test.test_suites.user_page_test_suite import UserPageTestSuite
from selenium_ui_test.test_suites.collections_test_suite import CollectionsTestSuite
from selenium_ui_test.test_suites.graph_test_suite import GraphTestSuite
from selenium_ui_test.test_suites.query_test_suite import QueryTestSuite
from selenium_ui_test.test_suites.views_test_suite import ViewsTestSuite

from selenium_ui_test.test_suites.analyzers_test_suite import AnalyzersTestSuite


class BasicTestSuite(BaseTestSuite):
    def __init__(self, selenium_runner):
        super().__init__(
            selenium_runner,
            child_classes=[
                UserPageTestSuite,
                # CollectionsTestSuite,
                # DashboardTestSuite,
                # ViewsTestSuite,
                # GraphTestSuite,
                # QueryTestSuite,
                # AnalyzersTestSuite,
            ],
        )
