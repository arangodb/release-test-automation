from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite

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


class BasicTestSuite(BaseTestSuite):
    def __init__(self, selenium_runner):
        super().__init__(
            selenium_runner,
            child_classes=[
                UserPageTestSuite,
                CollectionsTestSuite,
                ViewsTestSuite,
                GraphTestSuite,
                QueryTestSuite,
                AnalyzersTestSuite,
                DatabaseTestSuite,
                LogInTestSuite,

                DashboardTestSuite,
                SupportTestSuite,
            ],
        )
