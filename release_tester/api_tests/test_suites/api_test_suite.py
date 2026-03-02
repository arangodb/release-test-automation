""" API tests base class """
import json

import api_tests.helpers.request_helper as request_helper

from pathlib import Path

from semver import VersionInfo
from beautifultable import BeautifulTable

from reporting.reporting_utils import AllureTestSuiteContext
from test_suites_core.base_test_suite import BaseTestSuite


class APITestSuite(BaseTestSuite):
    """base class for API test suites"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, starter_instance):
        super().__init__()
        self.starter_instance = starter_instance
        self.current_version = VersionInfo.parse(starter_instance.cfg.version)
        self.sub_suite_name = self.__doc__ or self.__class__.__name__
        self.requests_data = {}
        requests_data_json_path = f"{Path(__file__).parent.parent.resolve()}/request_data/requests.json"
        with open(requests_data_json_path, "r", encoding="utf-8") as file:
            self.requests_data = json.load(file)

    def _init_allure(self):
        self.test_suite_context = AllureTestSuiteContext(
            sub_suite_name=self.sub_suite_name, inherit_test_suite_name=True, inherit_parent_test_suite_name=True
        )

    def run_test_suites(self, suites):
        """run all test suites from a given list"""
        for suite_class in suites:
            test_suite = suite_class(self.starter_instance)
            self.test_results += test_suite.run()

    def run_api_tests(self):
        """set up the test suites"""
        from api_tests.test_suites.test_suites import TestSuites

        self.run_test_suites(TestSuites.test_suites)
        # show api test results summary
        self.display_results_table()
        return all([result.success for result in self.test_results])

    def execute_request(self, request_data, use_arangosh=False):
        """execute http request"""
        if use_arangosh:
            return request_helper.execute_request_arangosh(self.starter_instance, request_data)
        return request_helper.execute_request_python(self.starter_instance, request_data)

    def display_results_table(self):
        """display the results of the test run"""
        api_test_results_table = BeautifulTable(maxwidth=160)
        api_test_results_table.set_style(BeautifulTable.STYLE_BOX_ROUNDED)
        for result in sorted(self.test_results, key=lambda res: res.name):
            api_test_results_table.rows.append(
                [result.name, "PASSED" if result.success else "FAILED", result.message, result.traceback]
            )
        api_test_results_table.columns.header = ["API Tests", "Result", "Message", "Traceback"]
        api_test_results_table.columns.header.alignment = BeautifulTable.ALIGN_CENTER
        api_test_results_table.columns.alignment["API Tests"] = BeautifulTable.ALIGN_LEFT
        print(f"\n{str(api_test_results_table)}")
