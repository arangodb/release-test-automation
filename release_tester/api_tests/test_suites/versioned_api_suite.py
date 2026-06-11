#!/usr/bin/env python3
"""versioned api test suite"""
import inspect

import api_tests.helpers.request_helper as rh

from semver import VersionInfo

from api_tests.test_suites.api_test_suite import APITestSuite
from test_suites_core.base_test_suite import testcase, run_before_suite, run_after_suite, run_before_each_testcase

HTTP_OK_CODES = [200, 201, 202]
MIN_ARANGO_VERSION = VersionInfo.parse("3.12.8")
A0_API_ARANGO_VERSION = VersionInfo.parse("3.12.8")
A1_API_ARANGO_VERSION = VersionInfo.parse("4.0.0")
A0_API_VERSION = "v0"
A1_API_VERSION = "v1"


class VersionedAPITestSuite(APITestSuite):
    """API Tests - Versioned api tests"""

    def __init__(self, starter_instance):
        super().__init__(starter_instance)
        if self.current_version < MIN_ARANGO_VERSION:
            self.__class__.is_disabled = True
            # pylint: disable=no-member
            self.__class__.disable_reasons.append("Test suite is only applicable to versions 3.12.8 and newer.")
        self.requests_data = self.requests_data[self.__class__.__name__]

    @testcase("2.1 Versioned API - supported API versions to Arango version mapping")
    def test_api_arango_version_mapping(self):
        """api versions to arango version mapping"""

        request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request_result = self.execute_request(request_data)["json"]
        # verify response contains info on supported, deprecated and requested APIs
        assert {"apiVersions", "deprecatedApiVersions", "requestedApiVersion"}.issubset(request_result.keys())
        # verify correct supported and requested API versions are returned depending on Arango version
        if self.current_version < A1_API_ARANGO_VERSION:
            assert request_result["apiVersions"] == [A0_API_VERSION]
            assert request_result["requestedApiVersion"] == A0_API_VERSION
        else:
            assert request_result["apiVersions"] == [A1_API_VERSION, A0_API_VERSION]
            assert request_result["requestedApiVersion"] == A1_API_VERSION

    @testcase("2.2 Versioned API - API paths with and without API prefix are supported")
    def test_api_paths_with_wo_prefix(self):
        """api paths with and without api prefix are supported"""

        request1_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
        request2_data = rh.clone_request_data(request1_data)
        latest_api_version = self.get_supported_api_versions()[0]
        request1_data = rh.update_request_data(
            request1_data, VersionedAPITestSuite.get_api_version_prefix(latest_api_version)
        )
        request2_data = rh.update_request_data(request2_data, "")
        request1_result = self.execute_request(request1_data)
        request2_result = self.execute_request(request2_data)
        # verify response codes are in 20x range for both requests
        assert request1_result["code"] in HTTP_OK_CODES
        assert request2_result["code"] in HTTP_OK_CODES

    @testcase("2.3 Versioned API - API version v1 is not supported in Arango 3.12.8+")
    def test_api_v1_in_arango_3_12(self):
        """v1 API is not supported in Arango 3.12.8+"""

        if self.current_version < A1_API_ARANGO_VERSION:
            request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
            request_data = rh.update_request_data(
                request_data, VersionedAPITestSuite.get_api_version_prefix(A1_API_VERSION)
            )
            request_result = self.execute_request(request_data)
            # verify response codes is 404 (Not found)
            assert request_result["code"] == 404

    @testcase("2.4 Versioned API - API version v0 is not supported in Arango 4.0.0+")
    def test_api_v0_in_arango_4(self):
        """v0 API is not supported in Arango 4.0.0+"""

        if self.current_version >= A1_API_ARANGO_VERSION:
            request_data = self.requests_data[str(inspect.currentframe().f_code.co_name)]
            request_data = rh.update_request_data(
                request_data, VersionedAPITestSuite.get_api_version_prefix(A0_API_VERSION)
            )
            request_result = self.execute_request(request_data)
            # verify response codes is 404 (Not found)
            assert request_result["code"] == 404

    def get_supported_api_versions(self):
        request_data = self.requests_data["get_api_version"]
        return self.execute_request(request_data)["json"]["apiVersions"]

    @staticmethod
    def get_api_version_prefix(api_version):
        return f"/_arango/{api_version}"
