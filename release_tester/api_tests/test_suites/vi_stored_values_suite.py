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

    @testcase("1. VI with stored values - simple query (stored values)")
    def test_vi_with_stored_values_simple_query(self):
        """simple query with stored values"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        # verify result count
        assert query_result["count"] == 2
        # verify filtering by numeric field
        values = self.get_elem_values_by_prop(query_result["result"], "val")
        assert all([(val < 5) for val in values]), "Numeric field filter was not applied correctly"
        # verify filtering by string field
        values = self.get_elem_values_by_prop(query_result["result"], "stringField")
        assert all([(val == "type_A") for val in values]), "String field filter was not applied correctly"
        # verify results sorted by distance
        values = self.get_elem_values_by_prop(query_result["result"], "dist")
        assert all([el1 == el2 for el1, el2 in zip(values, sorted(values))]), "Distances not ascending"

    @testcase("2. VI with stored values - simple query execution plan (stored values)")
    def test_vi_with_stored_values_simple_query_exec_plan(self):
        """execution plan for simple query with stored values filtering"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        # verify no separate filter node
        assert not self.has_elem_with_prop_value(query_result["plan"]["nodes"],
                                                  "type","FilterNode")
        # verify coverage by stored values
        index_node = self.find_elem_by_prop_value(query_result["plan"]["nodes"],
                                                  "type","EnumerateNearVectorNode")
        assert index_node["isCoveredByStoredValues"]
        # verify correct optimization rules are applied
        expected_rules = {"move-filters-into-enumerate", "use-vector-index"}
        assert expected_rules.issubset(
            set(query_result["plan"]["rules"])
        ), f"expected rules: {expected_rules} were not applied!"

    @testcase("3. VI with stored values - simple query (non-stored values)")
    def test_vi_with_stored_values_simple_query_non_stored_values(self):
        """simple query with non-stored values filtering"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        # verify result count
        assert query_result["count"] == 5
        # verify filtering by numeric field
        values = self.get_elem_values_by_prop(query_result["result"], "nonStoredValue")
        assert all([(val < 50) for val in values]), "Numeric field filter was not applied correctly"
        # verify results sorted by distance
        values = self.get_elem_values_by_prop(query_result["result"], "dist")
        assert all([el1 == el2 for el1, el2 in zip(values, sorted(values))]), "Distances not ascending"

    @testcase("4. VI with stored values - simple query execution plan (non-stored values)")
    def test_vi_with_stored_values_simple_query_exec_plan_non_stored_values(self):
        """execution plan for simple query with non-stored values filtering"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        # verify no separate filter node
        assert not self.has_elem_with_prop_value(query_result["plan"]["nodes"],
                                                  "type","FilterNode")
        # verify no coverage for non-stored values
        index_node = self.find_elem_by_prop_value(query_result["plan"]["nodes"],
                                                  "type","EnumerateNearVectorNode")
        assert not index_node["isCoveredByStoredValues"]

    @testcase("5. VI with stored values - complex query (stored values)")
    def test_vi_with_stored_values_complex_query(self):
        """complex query with stored values filtering"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        # verify result count
        assert query_result["count"] == 10
        # verify filtering by numeric field
        values = self.get_elem_values_by_prop(query_result["result"], "val")
        assert all([(2 <= val <= 50) for val in values]), "Numeric field filter was not applied correctly"
        # verify filtering by boolean field
        values = self.get_elem_values_by_prop(query_result["result"], "boolField")
        assert all([(val == True) for val in values]), "Boolean field filter was not applied correctly"
        # verify filtering by float field
        values = self.get_elem_values_by_prop(query_result["result"], "floatField")
        assert all([(val >= 10.0) for val in values]), "Numeric field filter was not applied correctly"
        # verify results sorted by distance
        values = self.get_elem_values_by_prop(query_result["result"], "dist")
        assert all([el1 == el2 for el1, el2 in zip(values, sorted(values))]), "Distances not ascending"

    @testcase("6. VI with stored values - complex query execution plan (stored values)")
    def test_vi_with_stored_values_complex_query_exec_plan(self):
        """execution plan for complex query with stored values filtering"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        # verify no separate filter node
        assert not self.has_elem_with_prop_value(query_result["plan"]["nodes"],
                                                  "type","FilterNode")
        # verify coverage by stored values
        index_node = self.find_elem_by_prop_value(query_result["plan"]["nodes"],
                                                  "type","EnumerateNearVectorNode")
        assert index_node["isCoveredByStoredValues"]
        # verify correct optimization rules are applied
        expected_rules = {"move-filters-into-enumerate", "use-vector-index"}
        assert expected_rules.issubset(
            set(query_result["plan"]["rules"])
        ), f"expected rules: {expected_rules} were not applied!"

    @testcase("7. VI with stored values - complex query (non-stored values)")
    def test_vi_with_stored_values_complex_query_non_stored_values(self):
        """complex query with non-stored values filtering"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        # verify result count
        assert query_result["count"] == 4
        # verify filtering by numeric field
        values = self.get_elem_values_by_prop(query_result["result"], "val")
        assert all([(10 <= val <= 50) for val in values]), "Numeric field filter was not applied correctly"
        # verify filtering by array field
        values = self.get_elem_values_by_prop(query_result["result"], "arrayField")
        assert all([(val[0] > 2) for val in values]), "Array field filter was not applied correctly"
        # verify filtering by object field
        values = self.get_elem_values_by_prop(query_result["result"], "objectField")
        assert all([(val["nested"] == 1) for val in values]), "Object nested field filter was not applied correctly"
        # verify results sorted by distance
        values = self.get_elem_values_by_prop(query_result["result"], "dist")
        assert all([el1 == el2 for el1, el2 in zip(values, sorted(values))]), "Distances not ascending"

    @testcase("8. VI with stored values - complex query execution plan (non-stored values)")
    def test_vi_with_stored_values_complex_query_exec_plan_non_stored_values(self):
        """execution plan for complex query with non-stored values filtering"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_data["payload"] = self.update_request_payload(request_data["payload"], self.collection)
        query_result = self.execute_request(request_data)[0].json()
        # verify no separate filter node
        assert not self.has_elem_with_prop_value(query_result["plan"]["nodes"],
                                                  "type","FilterNode")
        # verify no coverage for non-stored values
        index_node = self.find_elem_by_prop_value(query_result["plan"]["nodes"],
                                                  "type","EnumerateNearVectorNode")
        assert not index_node["isCoveredByStoredValues"]
