"""Operator integration tests: common test suite"""

import json
from pathlib import Path

import operator_integration_tests.helpers.request_helper as rh
import operator_integration_tests.helpers.general_helper as gh

from operator_integration_tests.base.operator_integration_base import OperatorIntegrationBaseTestSuite
from test_suites_core.base_test_suite import testcase, run_before_each_testcase, run_after_each_testcase
from reporting.reporting_utils import step

# pylint: disable=import-error
from test_suites_core.cli_test_suite import CliTestSuiteParameters
from operator_integration_tests.helpers.rbac_helper import RBACHelper

USER_TYPES = ["superuser", "user"]
HTTP_OK_CODES = [200, 201, 202]


class OperatorIntegrationCommonTestSuite(OperatorIntegrationBaseTestSuite):
    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.suite_name = "Operator integration tests (RBAC enabled system)"
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

    def create_test_user_and_create_test_data(self):
        """Create user, generate user token and create test data"""
        if self.user_name is None:
            self.user_name = gh.generate_username()
            # create new regular user
            request_data = self.requests_data["users"]["create_user"]
            request_data = rh.update_request_data(
                request_data, payload_param_1=self.user_name, payload_param_2=self.user_name, auth_token=self.su_token
            )
            rh.execute_request(request_data, self.arangod_url)
            # create user token
            self.user_token = self.rbh.generate_token(USER_TYPES[1], user_name=self.user_name)
            # create test data
            response_codes = []
            user = self.user_name
            policy_1 = "read-db"
            policy_2 = "use-api"
            role = "db-reader"
            # create default policies
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
            # create default role
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
            # create default role binding
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
            print(
                f"{'>>> Test data created successfully' if self.test_setup_ok else '!!! Error while test data creation'}"
            )

    def test_management_user_permissions_validation(self):
        """User permission validation"""
        if self.test_setup_ok:
            with step("validate user's permissions for specified resource"):
                policy = "read-db"
                policy_data = self.test_data["policies"][policy]
                request_data = self.requests_data["management api - permission validation"]["validate_permissions"]
                request_data = rh.update_request_data(
                    request_data,
                    payload_param_1=policy_data["actions"][0],
                    payload_param_2=policy_data["resources"][0],
                    auth_token=self.user_token,
                )
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                assert request_result["json"]["effect"] == "Allow"

    def test_e2e_list_collections_with_previously_bound_role(self):
        """User with correct role binding can list collections"""
        if self.test_setup_ok:
            with step("user with 'db-reader' role can list collections"):
                request_data = self.requests_data["collections"]["list_collections"]
                request_data = rh.update_request_data(request_data, auth_token=self.user_token)
                request_result = rh.execute_request(request_data, self.arangod_url)
                assert request_result["code"] == 200

    def test_management_policy_crud(self):
        """Policy management CRUD"""
        if self.test_setup_ok:
            with step("list existing policies"):
                request_data = self.requests_data["management api - policy"]["list_policies"]
                request_data = rh.update_request_data(request_data, auth_token=self.su_token)
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                assert set(request_result["json"]["names"]).issubset(set(self.test_data["policies"].keys()))

            with step("get detailed info on the particular policy"):
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

            with step("create a new policy"):
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

            with step("update a policy"):
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

            with step("delete a policy"):
                policy = "write-db"
                request_data = self.requests_data["management api - policy"]["delete_policy"]
                request_data = rh.update_request_data(request_data, endpoint_param_1=policy, auth_token=self.su_token)
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                with step("verify policy is deleted"):
                    policy = "write-db"
                    request_data = self.requests_data["management api - policy"]["get_policy_info"]
                    request_data = rh.update_request_data(
                        request_data, endpoint_param_1=policy, auth_token=self.su_token
                    )
                    request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                    assert request_result["code"] == 404
                    assert request_result["json"]["message"] == "Policy not found"

    def test_management_role_crud(self):
        """Role management CRUD"""
        if self.test_setup_ok:
            with step("list existing roles"):
                request_data = self.requests_data["management api - role"]["list_roles"]
                request_data = rh.update_request_data(request_data, auth_token=self.su_token)
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                assert set(request_result["json"]["names"]).issubset(set(self.test_data["roles"].keys()))

            with step("get detailed info on the particular role"):
                role = "db-reader"
                role_data = self.test_data["roles"][role]
                request_data = self.requests_data["management api - role"]["get_role_info"]
                request_data = rh.update_request_data(request_data, endpoint_param_1=role, auth_token=self.su_token)
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                assert request_result["json"]["name"] == role
                role_policies = request_result["json"]["item"]["policies"]
                assert set(role_policies) == set(role_data["policies"])

            with step("create a new role"):
                with step("create a new policy 'db-writer' for the future new role"):
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
                    rh.execute_request(request_data, self.rbh.sidecar_url)
                # create a new role with 'write-db' and 'use-api' policies
                role = "db-writer"
                role_data = self.test_data["roles"][role]
                request_data = self.requests_data["management api - role"]["create_role"]
                request_data = rh.update_request_data(
                    request_data,
                    payload_param_1=role_data["policies"][0],
                    payload_param_2=role_data["policies"][1],
                    endpoint_param_1=role,
                    auth_token=self.su_token,
                )
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                assert request_result["json"]["name"] == role
                role_policies = request_result["json"]["item"]["policies"]
                assert set(role_policies) == set(role_data["policies"])

            with step("update a role"):
                role = "db-writer"
                role_data = self.test_data["roles"][role]
                request_data = self.requests_data["management api - role"]["update_role"]
                request_data = rh.update_request_data(
                    request_data,
                    payload_param_1="read-db",
                    payload_param_2=role_data["policies"][1],
                    endpoint_param_1=role,
                    auth_token=self.su_token,
                )
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                assert request_result["json"]["name"] == role
                role_policies = request_result["json"]["item"]["policies"]
                assert set(role_policies) == {"read-db", role_data["policies"][1]}

            with step("delete a role"):
                role = "db-writer"
                request_data = self.requests_data["management api - role"]["delete_role"]
                request_data = rh.update_request_data(request_data, endpoint_param_1=role, auth_token=self.su_token)
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                with step("verify role is deleted"):
                    role = "db-writer"
                    request_data = self.requests_data["management api - role"]["get_role_info"]
                    request_data = rh.update_request_data(request_data, endpoint_param_1=role, auth_token=self.su_token)
                    request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                    assert request_result["code"] == 404
                    assert request_result["json"]["message"] == "Role not found"

    def test_management_role_binding_crud(self):
        """Role binding management CRUD"""
        if self.test_setup_ok:
            with step("list existing role bindings for a user"):
                role_binding, role = "db-reader", "db-reader"
                role_binding_data = self.test_data["role bindings"][role_binding]
                request_data = self.requests_data["management api - role binding"]["list_role_bindings"]
                request_data = rh.update_request_data(
                    request_data, endpoint_param_1=self.user_name, auth_token=self.su_token
                )
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                user_role_bindings_data = request_result["json"]["bindings"][0]
                assert user_role_bindings_data["role"] == role
                assert user_role_bindings_data["scope"]["statements"][0]["effect"] == role_binding_data["effect"]
                assert (
                    user_role_bindings_data["scope"]["statements"][0]["actions"][0] == role_binding_data["actions"][0]
                )
                assert (
                    user_role_bindings_data["scope"]["statements"][0]["resources"][0]
                    == role_binding_data["resources"][0]
                )

            with step("create a new role binding for existing regular user"):
                with step("create a new policy 'db-writer' for the future new role"):
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
                    rh.execute_request(request_data, self.rbh.sidecar_url)
                with step("create a new role with 'write-db' and 'use-api' policies for the new role binding"):
                    role = "db-writer"
                    role_data = self.test_data["roles"][role]
                    request_data = self.requests_data["management api - role"]["create_role"]
                    request_data = rh.update_request_data(
                        request_data,
                        payload_param_1=role_data["policies"][0],
                        payload_param_2=role_data["policies"][1],
                        endpoint_param_1=role,
                        auth_token=self.su_token,
                    )
                    rh.execute_request(request_data, self.rbh.sidecar_url)
                # create a new role binding for existing regular user
                role_binding, role = "db-writer", "db-writer"
                role_binding_data = self.test_data["role bindings"][role_binding]
                request_data = self.requests_data["management api - role binding"]["create_role_binding"]
                request_data = rh.update_request_data(
                    request_data,
                    payload_param_1=role_binding_data["effect"],
                    payload_param_2=role_binding_data["actions"][0],
                    payload_param_3=role_binding_data["resources"][0],
                    endpoint_param_1=self.user_name,
                    endpoint_param_2=role,
                    auth_token=self.su_token,
                )
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                assert request_result["json"]["user"] == self.user_name
                assert request_result["json"]["role"] == role
                assert request_result["json"]["scope"]["statements"][0]["effect"] == role_binding_data["effect"]
                assert request_result["json"]["scope"]["statements"][0]["actions"][0] == role_binding_data["actions"][0]
                assert (
                    request_result["json"]["scope"]["statements"][0]["resources"][0]
                    == role_binding_data["resources"][0]
                )

            with step("update a role binding"):
                role_binding, role = "db-writer", "db-writer"
                role_binding_data = self.test_data["role bindings"][role_binding]
                request_data = self.requests_data["management api - role binding"]["update_role_binding"]
                request_data = rh.update_request_data(
                    request_data,
                    payload_param_1="Deny",
                    payload_param_2=role_binding_data["actions"][0],
                    payload_param_3=role_binding_data["resources"][0],
                    endpoint_param_1=self.user_name,
                    endpoint_param_2=role,
                    auth_token=self.su_token,
                )
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                assert request_result["json"]["user"] == self.user_name
                assert request_result["json"]["role"] == role
                assert request_result["json"]["scope"]["statements"][0]["effect"] == "Deny"
                assert request_result["json"]["scope"]["statements"][0]["actions"][0] == role_binding_data["actions"][0]
                assert (
                    request_result["json"]["scope"]["statements"][0]["resources"][0]
                    == role_binding_data["resources"][0]
                )

            with step("delete a role binding"):
                role_binding, role = "db-writer", "db-writer"
                request_data = self.requests_data["management api - role binding"]["delete_role_binding"]
                request_data = rh.update_request_data(
                    request_data, endpoint_param_1=self.user_name, endpoint_param_2=role, auth_token=self.su_token
                )
                request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                assert request_result["code"] == 200
                with step("verify role is no longer bound to user"):
                    role_binding, role = "db-writer", "db-writer"
                    request_data = self.requests_data["management api - role binding"]["list_role_bindings"]
                    request_data = rh.update_request_data(
                        request_data, endpoint_param_1=self.user_name, auth_token=self.su_token
                    )
                    request_result = rh.execute_request(request_data, self.rbh.sidecar_url)
                    assert request_result["code"] == 200
                    user_role_bindings_data = request_result["json"]["bindings"]
                    assert role not in [binding["role"] for binding in user_role_bindings_data]

    def test_integration_api_authentication(self):
        """Integration API: Authentication endpoints"""
        with step("authenticated users can see their name extracted from the token - /identity"):
            request_data = self.requests_data["integration api - authentication"]["get_user_identity"]
            request_data = rh.update_request_data(request_data, auth_token=self.user_token)
            request_result = rh.execute_request(request_data, self.rbh.integration_url)
            assert request_result["code"] not in HTTP_OK_CODES

        with step("users can check their token validity - /validate"):
            request_data = self.requests_data["integration api - authentication"]["validate_token"]
            request_data = rh.update_request_data(request_data, payload_param_1=self.user_token)
            request_result = rh.execute_request(request_data, self.rbh.integration_url)
            assert request_result["code"] == 200
            assert request_result["json"]["isValid"]
            assert {"lifetime", "user", "groups"} == set(request_result["json"]["details"].keys())
            assert request_result["json"]["details"]["user"] == self.user_name

        with step("perform login (obtain a user token for browser-based flows) - /login"):
            request_data = self.requests_data["integration api - authentication"]["do_login"]
            request_data = rh.update_request_data(
                request_data, payload_param_1=self.user_name, payload_param_2=self.user_name
            )
            request_result = rh.execute_request(request_data, self.rbh.integration_url)
            assert request_result["code"] == 200
            assert "token" in request_result["json"]

        with step("perform logout (clears cookies, redirects to the login page) - /logout"):
            request_data = self.requests_data["integration api - authentication"]["do_logout"]
            request_data = rh.update_request_data(request_data, auth_token=self.user_token)
            request_result = rh.execute_request(request_data, self.rbh.integration_url)
            assert request_result["code"] == 200

        with step("create a new token for the specified user - /createToken"):
            request_data = self.requests_data["integration api - authentication"]["create_token"]
            request_data = rh.update_request_data(request_data, payload_param_1=self.user_name, payload_param_2="3600")
            request_result = rh.execute_request(request_data, self.rbh.integration_url)
            assert request_result["code"] == 200
            assert {"lifetime", "user", "token", "groups"} == set(request_result["json"].keys())
            assert request_result["json"]["user"] == self.user_name

    def test_integration_api_authorization(self):
        """Integration API: Authorization endpoints"""
        with step("evaluate a single set of permissions for a given user/role combination - /evaluate"):
            role = "db-reader"
            request_data = self.requests_data["integration api - authorization"]["evaluate_user_permission"]
            request_data = rh.update_request_data(request_data, payload_param_1=self.user_name, payload_param_2=role)
            request_result = rh.execute_request(request_data, self.rbh.integration_url)
            assert request_result["code"] == 200
            assert request_result["json"]["message"] == "Access Granted"
            assert request_result["json"]["effect"] == "Allow"

        with step("evaluate multiple sets of permissions for a given user/role combination -  /evaluate-many"):
            role = "db-reader"
            request_data = self.requests_data["integration api - authorization"]["evaluate_user_permissions"]
            request_data = rh.update_request_data(request_data, payload_param_1=self.user_name, payload_param_2=role)
            request_result = rh.execute_request(request_data, self.rbh.integration_url)
            assert request_result["code"] == 200
            assert request_result["json"]["message"] == "Access Granted"
            assert request_result["json"]["effect"] == "Allow"
            assert all([item["message"] == "Access Granted" for item in request_result["json"]["items"]])
            assert all([item["effect"] == "Allow" for item in request_result["json"]["items"]])

        with step("evaluate a single set of permissions for a given user token - /evaluate-token"):
            request_data = self.requests_data["integration api - authorization"]["evaluate_token_permission"]
            request_data = rh.update_request_data(request_data, payload_param_1=self.user_token)
            request_result = rh.execute_request(request_data, self.rbh.integration_url)
            assert request_result["code"] == 200
            assert request_result["json"]["message"] == "Access Granted"
            assert request_result["json"]["effect"] == "Allow"

        with step("evaluate multiple sets of permissions for a given user token - /evaluate-token-many"):
            request_data = self.requests_data["integration api - authorization"]["evaluate_token_permissions"]
            request_data = rh.update_request_data(request_data, payload_param_1=self.user_token)
            request_result = rh.execute_request(request_data, self.rbh.integration_url)
            assert request_result["code"] == 200
            assert request_result["json"]["message"] == "Access Granted"
            assert request_result["json"]["effect"] == "Allow"
            assert all([item["message"] == "Access Granted" for item in request_result["json"]["items"]])
            assert all([item["effect"] == "Allow" for item in request_result["json"]["items"]])

    def ensure_test_data_is_deleted(self):
        """Ensure that non-default policies and roles are deleted after each test"""
        if self.user_name is not None:
            # delete a role
            with step("delete role(s) created in tests"):
                role = "db-writer"
                request_data = self.requests_data["management api - role"]["delete_role"]
                request_data = rh.update_request_data(request_data, endpoint_param_1=role, auth_token=self.su_token)
                rh.execute_request(request_data, self.rbh.sidecar_url)
            # delete a policy
            with step("delete policy/-ies created in tests"):
                policy = "write-db"
                request_data = self.requests_data["management api - policy"]["delete_policy"]
                request_data = rh.update_request_data(request_data, endpoint_param_1=policy, auth_token=self.su_token)
                rh.execute_request(request_data, self.rbh.sidecar_url)
