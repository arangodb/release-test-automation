""" API tests base class """
import json
import requests

from pathlib import Path

from semver import VersionInfo

from reporting.reporting_utils import AllureTestSuiteContext
from test_suites_core.base_test_suite import BaseTestSuite

HTTP_METHODS = {"get": requests.get, "post": requests.post, "put": requests.put, "patch": requests.patch}


class APITestSuite(BaseTestSuite):
    """base class for API test suites"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, starter_instance):
        super().__init__()
        self.api_test_suites = []
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
            results = test_suite.run()
            self.test_results += results

    def run_api_tests(self):
        """set up the test suites"""
        from api_tests.test_suites.vi_stored_values_suite import VectorIndexStoredValuesTestSuite

        self.api_test_suites.append(VectorIndexStoredValuesTestSuite)
        self.run_test_suites(self.api_test_suites)
        # determine the outcome of API tests run
        overall_result = all([result.success for result in self.test_results])
        # if not overall_result:
        #     print([result for result in self.test_results if not result.success])
        return overall_result

    def execute_request(self, request_data):
        return self.starter_instance.send_request_json(
            HTTP_METHODS[request_data["method"]],
            request_data["endpoint"],
            json=request_data["payload"],
            headers=request_data["headers"],
        )

    def update_request_payload(self, request_payload, parameter):
        """update the request payload"""
        request_payload["query"] = request_payload["query"].replace("$1", parameter)
        return request_payload
