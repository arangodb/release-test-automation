# pylint: disable=duplicate-code
"""Operator integration tests: single server (base)"""

import shlex
import subprocess
from time import sleep

import operator_integration_tests.helpers.general_helper as gh

# pylint: disable=import-error
from arangodb.installers import RunProperties
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner, RunnerType
from arangodb.starter.deployments.none import NoStarter
from operator_integration_tests.base.operator_integration_base import OperatorIntegrationBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import run_before_suite, run_after_suite

from operator_integration_tests.helpers.rbac_helper import RBACHelper

ARANGOD_RBAC_ENDPOINT = "tcp://127.0.0.1:8529"
RBAC_SERVICE_GATEWAY = "http://127.0.0.1:9192"
STARTER_LAUNCH_DELAY = 10


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
            runner_type=RunnerType.SINGLE,
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
        self.runner.starter_prepare_env()
        self.starter = self.runner.starter_instance
        starter_args = [
            "--starter.mode single",
            f"--starter.data-dir {self.starter.basedir}",
            f"--auth.jwt-secret {self.jwt_dir / '-'}",
            "--starter.host 127.0.0.1",
            "--args.all.server.rest-server true",
            "--args.all.server.harden true",
            f"--args.all.server.external-rbac-service {RBAC_SERVICE_GATEWAY}",
            f"--args.all.server.jwt-secret-folder {self.jwt_dir}",
        ]
        print(starter_args)
        command = f"{self.starter.cfg.bin_dir / 'arangodb'} {' '.join(starter_args)}"
        self.starter.instance = subprocess.Popen(
            shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        print("starter instance:", self.starter.instance.pid)
        gh.delay_execution(STARTER_LAUNCH_DELAY)

    @run_before_suite
    def start_operator_services(self):
        """ensure operator binaries are available and start operator services"""
        RBACHelper.download_operator_binaries(self.operator_dir)
        RBACHelper.copy_operator_binary(self.operator_dir)
        # RBACHelper.copy_operator_integration_binary(self.operator_dir)
        self.rbh.start_operator_services(self.arangod_url)

    @run_after_suite
    def stop_operator_services(self):
        """stop operator services"""
        # self.rbh.stop_operator_services()
