#!/usr/bin/env python3
"""test suite for vector index with stored values verification"""
import inspect

import api_tests.helpers.request_helper as rh
import api_tests.helpers.payload_helper as ph
import api_tests.helpers.test_data_helper as tdh

from semver import VersionInfo

from api_tests.test_suites.api_test_suite import APITestSuite
from test_suites_core.base_test_suite import testcase, run_before_suite, run_after_suite

HTTP_OK_CODES = [200, 201, 202]
MIN_ARANGO_VERSION = VersionInfo.parse("3.12.7")
MAKE_DATA_COLLECTION = "c_vector_sv_0"
RTA_COLLECTION = "c_vector_sv_rta"
NUMBER_OF_DOCS = 4000


class VectorIndexStoredValuesTestSuite(APITestSuite):
    """API Tests - vector index with stored values"""

    def __init__(self, starter_instance):
        super().__init__(starter_instance)
        if self.current_version < MIN_ARANGO_VERSION:
            self.__class__.is_disabled = True
            # pylint: disable=no-member
            self.__class__.disable_reasons.append("Test suite is only applicable to versions 3.12.7 and newer.")
        self.requests_data = self.requests_data[self.__class__.__name__]
        self.collection = MAKE_DATA_COLLECTION if self.has_collection(MAKE_DATA_COLLECTION) else RTA_COLLECTION
        self.setup_ok = True
        self.rp = str(int(NUMBER_OF_DOCS / 2))

    @run_before_suite
    def create_collection_with_index(self):
        """create collection with docs and index if it doesn't exist"""
        if self.collection == RTA_COLLECTION:
            response_codes = []
            # create collection
            request_data = self.requests_data["create_collection"]
            request_data = rh.update_request_data(request_data, self.collection)
            response_codes.append(self.execute_request(request_data)["code"])
            # fill collection with documents
            request_data = self.requests_data["create_document"]
            request_data = rh.update_request_data(request_data, self.collection)
            request_data["payload"] = tdh.create_documents_with_vector_field(NUMBER_OF_DOCS)
            response_codes.append(self.execute_request(request_data)["code"])
            # create vector index with stored values
            request_data = self.requests_data["create_vector_index_with_stored_values"]
            request_data = rh.update_request_data(request_data, self.collection)
            response_codes.append(self.execute_request(request_data)["code"])
            self.setup_ok = all([code in HTTP_OK_CODES for code in response_codes])

    @testcase("1. VI with stored values - simple query (stored values)")
    def test_vi_with_stored_values_simple_query(self):
        """simple query with stored values"""

        if self.setup_ok:
            request1_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]["query"]
            request2_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]["plan"]
            request1_data = rh.update_request_data(request1_data, self.collection, self.rp)
            request2_data = rh.update_request_data(request2_data, self.collection, self.rp)
            request1_result = self.execute_request(request1_data)["json"]
            request2_result = self.execute_request(request2_data)["json"]
            # verify request1 (query) result
            # verify filtering by numeric field
            values = ph.get_elem_values_by_prop(request1_result["result"], "val")
            assert all([(val < 50) for val in values]), "Numeric field filter was not applied correctly"
            # verify filtering by string field
            values = ph.get_elem_values_by_prop(request1_result["result"], "stringField")
            assert all([(val == "type_A") for val in values]), "String field filter was not applied correctly"
            # verify results sorted by distance
            values = ph.get_elem_values_by_prop(request1_result["result"], "dist")
            assert all([el1 == el2 for el1, el2 in zip(values, sorted(values))]), "Distances not ascending"
            # verify request2 (plan) result
            # verify no separate filter node
            assert not ph.has_elem_with_prop_value(request2_result["plan"]["nodes"], "type", "FilterNode")
            # verify coverage by stored values
            index_node = ph.find_elem_by_prop_value(request2_result["plan"]["nodes"], "type", "EnumerateNearVectorNode")
            assert index_node["isCoveredByStoredValues"]
            # verify correct optimization rules are applied
            expected_rules = {"move-filters-into-enumerate", "use-vector-index"}
            assert expected_rules.issubset(
                set(request2_result["plan"]["rules"])
            ), f"expected rules: {expected_rules} were not applied!"

    @testcase("2. VI with stored values - simple query (non-stored values)")
    def test_vi_with_stored_values_simple_query_non_stored_values(self):
        """simple query with non-stored values filtering"""

        if self.setup_ok:
            request1_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]["query"]
            request2_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]["plan"]
            request1_data = rh.update_request_data(request1_data, self.collection, self.rp)
            request2_data = rh.update_request_data(request2_data, self.collection, self.rp)
            request1_result = self.execute_request(request1_data)["json"]
            request2_result = self.execute_request(request2_data)["json"]
            # verify request1 (query) result
            # verify filtering by numeric field
            values = ph.get_elem_values_by_prop(request1_result["result"], "nonStoredValue")
            assert all([(val < 50) for val in values]), "Numeric field filter was not applied correctly"
            # verify results sorted by distance
            values = ph.get_elem_values_by_prop(request1_result["result"], "dist")
            assert all([el1 == el2 for el1, el2 in zip(values, sorted(values))]), "Distances not ascending"
            # verify request2 (plan) result
            # verify no separate filter node
            assert not ph.has_elem_with_prop_value(request2_result["plan"]["nodes"], "type", "FilterNode")
            # verify no coverage for non-stored values
            index_node = ph.find_elem_by_prop_value(request2_result["plan"]["nodes"], "type", "EnumerateNearVectorNode")
            assert not index_node["isCoveredByStoredValues"]

    @testcase("3. VI with stored values - complex query (stored values)")
    def test_vi_with_stored_values_complex_query(self):
        """complex query with stored values filtering"""

        if self.setup_ok:
            request1_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]["query"]
            request2_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]["plan"]
            request1_data = rh.update_request_data(request1_data, self.collection, self.rp)
            request2_data = rh.update_request_data(request2_data, self.collection, self.rp)
            request1_result = self.execute_request(request1_data)["json"]
            request2_result = self.execute_request(request2_data)["json"]
            # verify request1 (query) result
            # verify filtering by numeric field
            values = ph.get_elem_values_by_prop(request1_result["result"], "val")
            assert all([(2 <= val <= 50) for val in values]), "Numeric field filter was not applied correctly"
            # verify filtering by boolean field
            values = ph.get_elem_values_by_prop(request1_result["result"], "boolField")
            assert all([(val == True) for val in values]), "Boolean field filter was not applied correctly"
            # verify filtering by float field
            values = ph.get_elem_values_by_prop(request1_result["result"], "floatField")
            assert all([(val > 10.0) for val in values]), "Numeric field filter was not applied correctly"
            # verify results sorted by distance
            values = ph.get_elem_values_by_prop(request1_result["result"], "dist")
            assert all([el1 == el2 for el1, el2 in zip(values, sorted(values))]), "Distances not ascending"
            # verify request2 (plan) result
            # verify no separate filter node
            assert not ph.has_elem_with_prop_value(request2_result["plan"]["nodes"], "type", "FilterNode")
            # verify coverage by stored values
            index_node = ph.find_elem_by_prop_value(request2_result["plan"]["nodes"], "type", "EnumerateNearVectorNode")
            assert index_node["isCoveredByStoredValues"]
            # verify correct optimization rules are applied
            expected_rules = {"move-filters-into-enumerate", "use-vector-index"}
            assert expected_rules.issubset(
                set(request2_result["plan"]["rules"])
            ), f"expected rules: {expected_rules} were not applied!"

    @testcase("4. VI with stored values - complex query (non-stored values)")
    def test_vi_with_stored_values_complex_query_non_stored_values(self):
        """complex query with non-stored values filtering"""

        if self.setup_ok:
            request1_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]["query"]
            request2_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]["plan"]
            request1_data = rh.update_request_data(request1_data, self.collection, self.rp)
            request2_data = rh.update_request_data(request2_data, self.collection, self.rp)
            request1_result = self.execute_request(request1_data)["json"]
            request2_result = self.execute_request(request2_data)["json"]
            # verify request1 (query) result
            # verify filtering by numeric field
            values = ph.get_elem_values_by_prop(request1_result["result"], "val")
            assert all([(10 <= val <= 50) for val in values]), "Numeric field filter was not applied correctly"
            # verify filtering by array field
            values = ph.get_elem_values_by_prop(request1_result["result"], "arrayField")
            assert all([(val[0] > 2) for val in values]), "Array field filter was not applied correctly"
            # verify filtering by object field
            values = ph.get_elem_values_by_prop(request1_result["result"], "objectField")
            assert all([(val["nested"] == 1) for val in values]), "Object nested field filter was not applied correctly"
            # verify results sorted by distance
            values = ph.get_elem_values_by_prop(request1_result["result"], "dist")
            assert all([el1 == el2 for el1, el2 in zip(values, sorted(values))]), "Distances not ascending"
            # verify request2 (plan) result
            # verify no separate filter node
            assert not ph.has_elem_with_prop_value(request2_result["plan"]["nodes"], "type", "FilterNode")
            # verify no coverage for non-stored values
            index_node = ph.find_elem_by_prop_value(request2_result["plan"]["nodes"], "type", "EnumerateNearVectorNode")
            assert not index_node["isCoveredByStoredValues"]

    @run_after_suite
    def drop_collection(self):
        """drop created collection after the tests completion"""
        if self.collection == RTA_COLLECTION:
            # drop collection
            request_data = self.requests_data["drop_collection"]
            request_data = rh.update_request_data(request_data, self.collection)
            self.execute_request(request_data)

    def has_collection(self, collection):
        request_data = self.requests_data["check_collection"]
        request_data = rh.update_request_data(request_data, collection)
        return self.execute_request(request_data)["code"] != 404
