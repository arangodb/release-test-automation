# pylint: disable=duplicate-code
"""Operator integration tests: single server (base)"""

# pylint: disable=import-error
from arangodb.installers import RunProperties
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner, RunnerType
from arangodb.starter.deployments.none import NoStarter
from operator_integration_tests.base.operator_integration_base import OperatorIntegrationBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import run_before_suite, run_after_suite

from operator_integration_tests.helpers.rbac_helper import RBACHelper
from operator_integration_tests.helpers.rbac_helper import RBAC_SERVICE_GATEWAY


class OperatorIntegrationSingleServerBaseTestSuite(OperatorIntegrationBaseTestSuite):
    """Operator integration tests: single server (base class)"""

    @run_before_suite
    def start(self):
        """start a single server setup before running tests"""
        self.start_single_server()

    # pylint: disable=attribute-defined-outside-init
    @step
    def start_single_server(self):
        """start a single server setup"""
        self.runner = make_runner(
            runner_type=RunnerType.SINGLE_RBAC,
            abort_on_error=False,
            installer_set=self.installer_set,
            selenium_worker="none",
            selenium_driver_args=[],
            selenium_include_suites=[],
            runner_properties=RunProperties(
                enterprise=True,
                encryption_at_rest=False,
                ssl=False,
            ),
        )
        self.rbh = self.runner.rbh
        self.su_token = self.runner.su_token
        self.runner.starter_prepare_env()
        self.runner.starter_run()
        self.runner.finish_setup()
        self.runner.starter_instance.detect_arangosh_instances(self.runner.starter_instance, self.runner.cfg.version)
        self.starter = self.runner.starter_instance
