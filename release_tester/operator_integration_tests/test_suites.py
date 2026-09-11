from copy import deepcopy

from operator_integration_tests.base.operator_integration_base import OperatorIntegrationBaseTestSuite
from operator_integration_tests.single_server import OperatorIntegrationSingleServerTestSuite
from test_suites_core.base_test_suite import run_before_suite, run_after_suite
from test_suites_core.cli_test_suite import CliTestSuiteParameters


class OperatorIntegrationTestSuite(OperatorIntegrationBaseTestSuite):

    child_test_suites = [OperatorIntegrationSingleServerTestSuite]

    def __init__(self, params: CliTestSuiteParameters):
        local_params = deepcopy(params)
        local_params.old_version = None
        super().__init__(local_params)

    @run_before_suite
    def install_package(self):
        """install server package"""
        self.installer.install_server_package()

    @run_after_suite
    def uninstall_package(self):
        """uninstall package"""
        self.installer.un_install_server_package()
        self.installer.cleanup_system()
