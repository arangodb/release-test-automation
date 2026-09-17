"""Operator integration tests: cluster"""

from operator_integration_tests.common_test_suite import OperatorIntegrationCommonTestSuite
from operator_integration_tests.base.cluster_base import OperatorIntegrationClusterBaseTestSuite
from test_suites_core.base_test_suite import testcase, run_before_each_testcase, run_after_each_testcase

# pylint: disable=import-error
from test_suites_core.cli_test_suite import CliTestSuiteParameters
from operator_integration_tests.helpers.rbac_helper import RBACHelper


class OperatorIntegrationClusterTestSuite(OperatorIntegrationCommonTestSuite, OperatorIntegrationClusterBaseTestSuite):
    """Operator integration tests: cluster"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)

    @run_before_each_testcase
    def create_test_user_and_create_test_data(self):
        """Create user, generate user token and create test data"""
        super().create_test_user_and_create_test_data()

    @testcase("1. Management API (validation): User permission validation - Cluster")
    def test_management_user_permissions_validation(self):
        """User permission validation - Cluster"""
        super().test_management_user_permissions_validation()

    @testcase(
        "2. Management API (policy, role, binding): User with correct role binding can list collections - Cluster"
    )
    def test_e2e_list_collections_with_previously_bound_role(self):
        """User with correct role binding can list collections - Cluster"""
        super().test_e2e_list_collections_with_previously_bound_role()

    @testcase("3. Management API (policy): Policy management CRUD - Cluster")
    def test_management_policy_crud(self):
        """Policy management CRUD - Cluster"""
        super().test_management_policy_crud()

    @testcase("4. Management API (role): Role management CRUD - Cluster")
    def test_management_role_crud(self):
        """Role management CRUD - Cluster"""
        super().test_management_role_crud()

    @testcase("5. Management API (role binding): Role binding management CRUD - Cluster")
    def test_management_role_binding_crud(self):
        """Role binding management CRUD - Cluster"""
        super().test_management_role_binding_crud()

    @testcase("6. Integration API: Authentication endpoints - Cluster")
    def test_integration_api_authentication(self):
        """Integration API: Authentication endpoints - Cluster"""
        super().test_integration_api_authentication()

    @testcase("7. Integration API: Authorization endpoints - Cluster")
    def test_integration_api_authorization(self):
        """Integration API: Authorization endpoints - Cluster"""
        super().test_integration_api_authorization()

    @run_after_each_testcase
    def ensure_test_data_is_deleted(self):
        """Ensure that non-default policies and roles are deleted after each test"""
        super().ensure_test_data_is_deleted()
