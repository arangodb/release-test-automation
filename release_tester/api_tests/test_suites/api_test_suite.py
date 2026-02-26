""" API tests base class """
import json
import requests

from pathlib import Path

from semver import VersionInfo
from beautifultable import BeautifulTable

from reporting.reporting_utils import AllureTestSuiteContext
from test_suites_core.base_test_suite import BaseTestSuite

HTTP_METHODS = {"get": requests.get, "post": requests.post, "put": requests.put, "patch": requests.patch}


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
        self.result_json_path = f"{Path(__file__).parent.parent.resolve()}/request_data/response.json"

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

    def execute_request(self, request_data, use_arangosh=True):
        """execute http request"""
        if use_arangosh:
            return self.execute_request_arangosh(request_data)
        return self.starter_instance.send_request_json(
            HTTP_METHODS[request_data["method"]],
            request_data["endpoint"],
            json=request_data["payload"],
            headers=request_data["headers"],
        )[0].json()

    @staticmethod
    def update_request_payload(request_payload, parameter):
        """update the request payload"""
        request_payload["query"] = request_payload["query"].replace("$1", parameter)
        return request_payload

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

    @staticmethod
    def has_elem_with_prop_value(elem_list, prop, val):
        """checks if element with property value exists"""
        return len([elem for elem in elem_list if elem[prop] == val]) > 0

    @staticmethod
    def find_elem_by_prop_value(elem_list, prop, val):
        """find element by property value"""
        return [elem for elem in elem_list if elem[prop] == val][0]

    @staticmethod
    def get_elem_values_by_prop(elem_list, prop):
        """get elem values for property"""
        return [elem[prop] for elem in elem_list if prop in elem]

    def execute_request_arangosh(self, request_data):
        """execute http request using arangosh"""
        fe_instance = [instance for instance in self.starter_instance.all_instances if instance.is_frontend()][0]
        base_url = fe_instance.get_public_plain_url()
        full_url = self.starter_instance.get_http_protocol() + "://" + base_url + request_data["endpoint"]

        js_script = """
            const fs = require('fs');
            const request = require('@arangodb/request');
            const res = request({
                method: '%s',
                url: '%s',
        """ % (request_data["method"], full_url)
        if 'headers' in request_data:
            js_script += """
                headers: %s,
            """ % (json.dumps(request_data["headers"]))
        if 'payload' in request_data:
            js_script += """
                body: %s,
                json: true,
           """ % (json.dumps(request_data["payload"]))
        js_script += """
                auth: {bearer: '%s'}
            });
            fs.write('%s', JSON.stringify(res));
        """ % (
            str(self.starter_instance.get_jwt_header()),
            self.result_json_path
        )
        self.starter_instance.arangosh.run_command(("execute http request in arangosh", js_script), verbose=False)
        result = {"body": "{}"}
        with open(self.result_json_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        return json.loads(result["body"])
