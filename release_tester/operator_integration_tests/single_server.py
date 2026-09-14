"""Operator integration tests: single server"""

import json
from pathlib import Path

import operator_integration_tests.helpers.request_helper as rh
import operator_integration_tests.helpers.general_helper as gh

from operator_integration_tests.base.single_server_base import OperatorIntegrationSingleServerBaseTestSuite
from test_suites_core.base_test_suite import testcase, run_before_suite, run_before_each_testcase

# pylint: disable=import-error
from test_suites_core.cli_test_suite import CliTestSuiteParameters
from operator_integration_tests.helpers.rbac_helper import RBACHelper

USER_TYPES = ["superuser", "user"]
HTTP_OK_CODES = [200, 201, 202]


class OperatorIntegrationSingleServerTestSuite(OperatorIntegrationSingleServerBaseTestSuite):
    """Operator integration tests: single server"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.suite_name = "Operator integration tests: Clean install"
        self.requests_data = {}
        requests_data_json_path = f"{Path(__file__).parent.resolve()}/request_data/requests.json"
        with open(requests_data_json_path, "r", encoding="utf-8") as file:
            self.requests_data = json.load(file)
        self.test_data = {}
        test_data_json_path = f"{Path(__file__).parent.resolve()}/test_data/test_data.json"
        with open(test_data_json_path, "r", encoding="utf-8") as file:
            self.test_data = json.load(file)
        self.su_token = self.rbh.generate_token(USER_TYPES[0])
        self.user_name = None
        self.user_token = None
        self.test_setup_ok = True

    @run_before_each_testcase
    def create_test_user_and_seed_test_data(self):
        """Create user, generate user token and seed test data"""
        if self.user_name is None:
            self.user_name = gh.generate_username()
            print(self.user_name)
            # create new regular user
            request_data = self.requests_data["users"]["create_user"]
            request_data = rh.update_request_data(
                request_data, payload_param_1=self.user_name, payload_param_2=self.user_name, auth_token=self.su_token
            )
            request_result = rh.execute_request(request_data, self.arangod_url)
            print(request_result)
            # create user token
            self.user_token = self.rbh.generate_token(USER_TYPES[1], user_name=self.user_name)
            # seed test data
            response_codes = []
            user = self.user_name
            policy_1 = "read-db"
            policy_2 = "use-api"
            role = "db-reader"
            # create policies
            print(f"Creating '{policy_1}' and '{policy_2}' policies...")
            request_data_1 = self.requests_data["management api - policy"]["create_policy"]
            request_data_2 = rh.clone_request_data(request_data_1)
            request_data_1 = rh.update_request_data(
                request_data_1,
                payload_param_1="Allow",
                payload_param_2="db:Read",
                payload_param_3="db:*",
                endpoint_param_1=policy_1,
                auth_token=self.su_token,
            )
            request_data_2 = rh.update_request_data(
                request_data_2,
                payload_param_1="Allow",
                payload_param_2="db:UseApiVersion",
                payload_param_3="db:apiversion:v0",
                endpoint_param_1=policy_2,
                auth_token=self.su_token,
            )
            response_codes.append(rh.execute_request(request_data_1, self.rbh.sidecar_url)["code"])
            response_codes.append(rh.execute_request(request_data_2, self.rbh.sidecar_url)["code"])
            # create role
            print(f"Creating '{role}' containing '{policy_1}' and '{policy_2}' policies...")
            request_data = self.requests_data["management api - role"]["create_role"]
            request_data = rh.update_request_data(
                request_data,
                payload_param_1=policy_1,
                payload_param_2=policy_2,
                endpoint_param_1=role,
                auth_token=self.su_token,
            )
            response_codes.append(rh.execute_request(request_data, self.rbh.sidecar_url)["code"])
            # create role binding
            print(f"Binding '{role}' role to '{user}'...")
            request_data = self.requests_data["management api - role binding"]["create_role_binding"]
            request_data = rh.update_request_data(
                request_data,
                payload_param_1="Allow",
                payload_param_2="*",
                payload_param_3="*",
                endpoint_param_1=user,
                endpoint_param_2=role,
                auth_token=self.su_token,
            )
            response_codes.append(rh.execute_request(request_data, self.rbh.sidecar_url)["code"])
            # give system time to sync changes
            gh.delay_execution()
            self.test_setup_ok = all([code in HTTP_OK_CODES for code in response_codes])

    @testcase("1. Management API (validation): User permission validation - Single server")
    def test_management_user_permissions_validation(self):
        """User permission validation - Single server"""
        if self.test_setup_ok:
            # validate user's permissions for specified resource
            request_data = self.requests_data["management api - permission validation"]["validate_permissions"]
            request_data = rh.update_request_data(
                request_data, payload_param_1="db:Read", payload_param_2="db:*", auth_token=self.user_token
            )
            request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
            assert request_result["code"] == 200
            assert request_result["json"]["effect"] == "Allow"

    @testcase(
        "2. Management API (policy, role, binding): User with correct role binding can list collections - Single server"
    )
    def test_e2e_bind_role_and_list_collections(self):
        """User with correct role binding can list collections - Single server"""
        if self.test_setup_ok:
            # list collections with regular user
            request_data = self.requests_data["collections"]["list_collections"]
            request_data = rh.update_request_data(request_data, auth_token=self.user_token)
            request_result = rh.execute_request(request_data, self.arangod_url)
            assert request_result["code"] == 200

    @testcase("3. Management API (policy): Policy management CRUD - Single server")
    def test_management_policy_crud(self):
        """Policy management CRUD - Single server"""
        if self.test_setup_ok:
            # list existing policies
            request_data = self.requests_data["management api - policy"]["list_policies"]
            request_data = rh.update_request_data(request_data, auth_token=self.su_token)
            request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
            assert request_result["code"] == 200
            assert set(request_result["json"]["names"]).issubset(set(self.test_data["policies"].keys()))
            # get detailed info on the particular policy
            policy = "use-api"
            policy_data = self.test_data["policies"][policy]
            request_data = self.requests_data["management api - policy"]["get_policy_info"]
            request_data = rh.update_request_data(request_data, endpoint_param_1=policy, auth_token=self.su_token)
            request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
            assert request_result["code"] == 200
            assert request_result["json"]["name"] == policy
            policy_permissions = request_result["json"]["item"]["statements"][0]
            assert policy_permissions["effect"] == policy_data["effect"]
            assert policy_permissions["actions"][0] == policy_data["actions"][0]
            assert policy_permissions["resources"][0] == policy_data["resources"][0]
            # create a new policy
            policy = "write-db"
            policy_data = self.test_data["policies"][policy]
            request_data = self.requests_data["management api - policy"]["create_policy"]
            request_data = rh.update_request_data(
                request_data,
                payload_param_1=policy_data["effect"],
                payload_param_2=policy_data["actions"][0],
                payload_param_3=policy_data["resources"][0],
                endpoint_param_1=policy,
                auth_token=self.su_token,
            )
            request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
            assert request_result["code"] == 200
            assert request_result["json"]["name"] == policy
            policy_permissions = request_result["json"]["item"]["statements"][0]
            assert policy_permissions["effect"] == policy_data["effect"]
            assert policy_permissions["actions"][0] == policy_data["actions"][0]
            assert policy_permissions["resources"][0] == policy_data["resources"][0]
            # update a policy
            policy = "write-db"
            policy_data = self.test_data["policies"][policy]
            request_data = self.requests_data["management api - policy"]["update_policy"]
            request_data = rh.update_request_data(
                request_data,
                payload_param_1="Deny",
                payload_param_2=policy_data["actions"][0],
                payload_param_3=policy_data["resources"][0],
                endpoint_param_1=policy,
                auth_token=self.su_token,
            )
            request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
            assert request_result["code"] == 200
            assert request_result["json"]["name"] == policy
            policy_permissions = request_result["json"]["item"]["statements"][0]
            assert policy_permissions["effect"] == "Deny"
            assert policy_permissions["actions"][0] == policy_data["actions"][0]
            assert policy_permissions["resources"][0] == policy_data["resources"][0]
            # delete a policy
            policy = "write-db"
            request_data = self.requests_data["management api - policy"]["delete_policy"]
            request_data = rh.update_request_data(request_data, endpoint_param_1=policy, auth_token=self.su_token)
            request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
            assert request_result["code"] == 200
            # verify policy is deleted
            policy = "write-db"
            request_data = self.requests_data["management api - policy"]["get_policy_info"]
            request_data = rh.update_request_data(request_data, endpoint_param_1=policy, auth_token=self.su_token)
            request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
            assert request_result["code"] == 404
            assert request_result["json"]["message"] == "Policy not found"

    @testcase("4. Integration API (Authentication): user token validation - Single server")
    def test_integration_user_token_validation(self):
        """Integration API (Authentication): user token validation - Single server"""
        request_data = self.requests_data["integration api - authentication"]["validate_token"]
        request_data = rh.update_request_data(request_data, payload_param_1=self.user_token)
        request_result = rh.execute_request(request_data, self.rbh.integration_url)
        print(request_result)
        assert request_result["code"] == 200
        assert request_result["json"]["details"]["user"] == self.user_name
