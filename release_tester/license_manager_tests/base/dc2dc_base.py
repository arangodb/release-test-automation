"""License manager tests: DC2DC"""
import json

import requests

# pylint: disable=import-error
from arangodb.installers import RunProperties
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner, RunnerType
from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import run_before_suite


class LicenseManagerDc2DcBaseTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: DC2DC"""

    def get_default_instance_type(self):
        """get the instance type we should communicate with"""
        return InstanceType.COORDINATOR

    @run_before_suite
    def startup(self):
        """prepare test environment to run license manager tests on a DC2DC setup"""
        self.start_clusters()

    @step
    def start_clusters(self):
        """start DC2DC setup"""
        # pylint: disable=attribute-defined-outside-init
        self.runner = make_runner(
            runner_type=RunnerType.DC2DC,
            abort_on_error=False,
            installer_set=self.installer_set,
            use_auto_certs=False,
            selenium_worker="none",
            selenium_driver_args=[],
            runner_properties=RunProperties(
                enterprise=True,
                encryption_at_rest=False,
                ssl=False,
            ),
        )
        self.runner.starter_prepare_env()
        self.runner.starter_run()
        self.runner.finish_setup()
        self.starter = self.runner.cluster1["instance"]

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
        resps = self.starter.send_request(
            InstanceType.AGENT,
            requests.post,
            "/_api/agency/write",
            body,
        )
        success = False
        for response in resps:
            if 200 <= response.status_code < 300:
                success = True
        assert success, "Failed to write license to agency."
