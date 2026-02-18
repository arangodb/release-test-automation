#!/usr/bin/env python3
"""test suite for vector index with stored values verification"""
import inspect

from semver import VersionInfo

from api_tests.test_suites.api_test_suite import APITestSuite
from test_suites_core.base_test_suite import testcase

MIN_ARANGO_VERSION = VersionInfo.parse("3.12.7")


class VectorIndexStoredValuesTestSuite(APITestSuite):
    """API Tests - vector index with stored values"""

    def __init__(self, starter_instance):
        super().__init__(starter_instance)
        self.collection = "c_vector_sv_0"
        self.requests_data = self.requests_data[self.__class__.__name__]
        if self.current_version < MIN_ARANGO_VERSION:
            self.__class__.is_disabled = True
            # pylint: disable=no-member
            self.__class__.disable_reasons.append("Test suite is only applicable to versions 3.12.7 and newer.")

    @testcase("Vector index with stored values API test 1 - query with stored values filtering")
    def test_aql_query_vector_index_with_stored_values(self):
        """query with stored values filtering"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        assert query_result["count"] == 2

    @testcase("Vector index with stored values API test 2 - execution plan for query with stored values filtering")
    def test_exec_plan_vector_index_with_stored_values(self):
        """execution plan for query with stored values filtering"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        expected_rules = {"move-filters-up", "move-filters-up-2", "use-vector-index"}
        assert expected_rules.issubset(
            set(query_result["plan"]["rules"])
        ), f"expected rules: {expected_rules} were not applied!"
