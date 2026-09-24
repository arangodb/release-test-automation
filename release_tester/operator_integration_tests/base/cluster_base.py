# pylint: disable=duplicate-code
"""Operator integration tests: cluster (base)"""

import shlex
import subprocess

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

RBAC_SERVICE_GATEWAY = "http://127.0.0.1:9192"
STARTER_LAUNCH_DELAY = 10
CLUSTER_LAUNCH_DELAY = 20


class OperatorIntegrationClusterBaseTestSuite(OperatorIntegrationBaseTestSuite):
    """Operator integration tests: cluster (base class)"""

    @run_before_suite
    def start(self):
        """start a local cluster setup before running tests"""
        self.start_cluster()

    # pylint: disable=attribute-defined-outside-init
    @step
    def start_cluster(self):
        """start a local cluster setup"""
        self.runner = make_runner(
            runner_type=RunnerType.CLUSTER,
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
        self.starter = self.runner.starter_instances[0]
        print("starting local cluster...")
        self.start_local_cluster()  # or self.start_single_starter_local_cluster()

    @run_before_suite
    def start_operator_services(self):
        """download operator binaries and start operator (RBAC) services"""
        self.rbh.start_operator_services(self.arangod_url)

    @run_after_suite
    def stop_operator_services(self):
        """stop operator (RBAC) services"""
        self.rbh.stop_operator_services()

    def start_single_starter_local_cluster(self):
        """start local test cluster using a single starter"""

        starter_args = ["--starter.local", f"--starter.data-dir {self.starter.basedir}", "--starter.host 127.0.0.1"]
        starter_args.extend(self.get_rbac_starter_params())
        command = f"{self.starter.cfg.bin_dir / 'arangodb'} {' '.join(starter_args)}"
        self.starter.instance = subprocess.Popen(
            shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        print(f"starter instance PID: << {self.starter.instance.pid} >> ")
        gh.delay_execution(CLUSTER_LAUNCH_DELAY)

    def start_local_cluster(self):
        """start local cluster with 3 starters"""

        starter_path = f"{self.starter.cfg.bin_dir / 'arangodb'}"
        starter_1, starter_2, starter_3 = self.runner.starter_instances
        starter_1_args = [f"--starter.data-dir {starter_1.basedir}"]
        starter_1_args.extend(self.get_rbac_starter_params())
        starter_1_command = f"{starter_path} {' '.join(starter_1_args)}"
        starter_1.instance = subprocess.Popen(
            shlex.split(starter_1_command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        print(f"starter instance 1 PID: << {starter_1.instance.pid} >>")
        gh.delay_execution(STARTER_LAUNCH_DELAY)
        starter_2_args = ["--starter.join=localhost", f"--starter.data-dir {starter_2.basedir}"]
        starter_2_args.extend(self.get_rbac_starter_params())
        starter_2_command = f"{starter_path} {' '.join(starter_2_args)}"
        starter_2.instance = subprocess.Popen(
            shlex.split(starter_2_command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        print(f"starter instance 2 PID: << {starter_2.instance.pid} >>")
        gh.delay_execution(STARTER_LAUNCH_DELAY)
        starter_3_args = ["--starter.join=localhost", f"--starter.data-dir {starter_3.basedir}"]
        starter_3_args.extend(self.get_rbac_starter_params())
        starter_3_command = f"{starter_path} {' '.join(starter_3_args)}"
        starter_3.instance = subprocess.Popen(
            shlex.split(starter_3_command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        print(f"starter instance 3 PID: << {starter_3.instance.pid} >>")
        gh.delay_execution(CLUSTER_LAUNCH_DELAY)

    def get_rbac_starter_params(self):
        """get rbac starter parameters"""

        starter_params = [
            f"--auth.jwt-secret {self.jwt_dir / '-'}",
            "--args.all.server.rest-server true",
            "--args.all.server.harden true",
            f"--args.all.server.external-rbac-service {RBAC_SERVICE_GATEWAY}",
            f"--args.all.server.jwt-secret-folder {self.jwt_dir}",
        ]
        return starter_params
