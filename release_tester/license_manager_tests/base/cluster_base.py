"""License manager tests: cluster"""
import json

import requests

# pylint: disable=import-error
from arangodb.installers import RunProperties
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner, RunnerType
from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import run_before_suite


class LicenseManagerClusterBaseTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: cluster"""

    def get_default_instance_type(self):
        """get the instance type we should communicate with"""
        return InstanceType.COORDINATOR

    @run_before_suite
    def startup(self):
        """prepare test environment to run license manager tests on a cluster setup"""
        self.start_cluster()

    @step
    def start_cluster(self):
        """start a cluster setup"""
        # pylint: disable=attribute-defined-outside-init
        self.runner = make_runner(
            runner_type=RunnerType.CLUSTER,
            abort_on_error=False,
            selenium_worker="none",
            selenium_driver_args=[],
            installer_set=self.installer_set,
            runner_properties=RunProperties(
                enterprise=True,
                encryption_at_rest=False,
                ssl=False,
            ),
            use_auto_certs=False,
        )
        self.runner.starter_prepare_env()
        self.runner.starter_run()
        self.runner.finish_setup()
        self.starter = self.runner.starter_instances[0]

    def get_server_id(self):
        """read server ids from agency"""
        resp = self.starter.send_request(
            InstanceType.COORDINATOR,
            requests.get,
            "/_api/cluster/agency-dump",
        )
        json_body = json.loads(resp[0].text)
        agent_list = list(json_body["agency"][".agency"]["pool"].keys())
        agent_list.sort()
        return "".join(agent_list)

    # pylint: disable=redefined-builtin
    def set_license(self, license):
        """set new license"""
        body = """[[{"/arango/.license":{"op":"set","new": """ + license + """}}]]"""
        resp = self.runner.agency_get_leader_starter_instance().send_request(
            InstanceType.AGENT,
            requests.post,
            "/_api/agency/write",
            body,
        )
        assert 200 <= resp[0].status_code < 300, "Failed to write license to agency."
