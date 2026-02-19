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

    @testcase("VI with stored values - query results (filtering and sorting)")
    def test_aql_query_vector_index_with_stored_values(self):
        """query with stored values filtering"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        # verify result count
        assert query_result["count"] == 2
        # verify filtering by numeric field
        values = self.get_elem_values_by_prop(query_result["result"], "val")
        assert all([(val < 5) for val in values]), "Numeric filter was not applied correctly"
        # verify filtering by string field
        values = self.get_elem_values_by_prop(query_result["result"], "stringField")
        assert all([(val == "type_A") for val in values]), "String filter was not applied correctly"
        # verify results sorted by distance
        values = self.get_elem_values_by_prop(query_result["result"], "dist")
        assert all([el1 == el2 for el1, el2 in zip(values, sorted(values))]), "Distances not ascending"



    @testcase("VI with stored values - execution plan (simple query)")
    def test_exec_plan_vector_index_with_stored_values(self):
        """execution plan for query with stored values filtering"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        # verify coverage by stored values
        index_node = self.find_elem_by_prop_value(query_result["plan"]["nodes"],
                                                  "type","EnumerateNearVectorNode")
        assert index_node["isCoveredByStoredValues"]
        # verify correct rules are applied
        expected_rules = {"move-filters-up", "move-filters-up-2", "use-vector-index"}
        assert expected_rules.issubset(
            set(query_result["plan"]["rules"])
        ), f"expected rules: {expected_rules} were not applied!"
