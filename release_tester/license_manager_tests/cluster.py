"""License manager tests: cluster"""
import json

import requests

# pylint: disable=import-error
from arangodb.installers import RunProperties
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner, RunnerType
from license_manager_tests.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import testcase, run_before_suite


class LicenseManagerClusterTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: cluster"""

    def get_default_instance_type(self):
        """get the instance type we should communicate with"""
        return InstanceType.RESILIENT_SINGLE

    @run_before_suite
    def startup(self):
        """prepare test env"""
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
        resp = self.runner.agency_get_leader().send_request(
            InstanceType.AGENT,
            requests.post,
            "/_api/agency/write",
            body,
        )
        assert 200 <= resp[0].status_code < 300, "Failed to write license to agency."

    @testcase
    def clean_install_temp_license(self):
        """Check that server gets a 60-minute license after installation on a clean system"""
        self.check_that_license_is_not_expired(50 * 60)

    @testcase
    def goto_read_only_mode_when_license_expired(self):
        """Check that system goes to read-only mode when license is expired"""
        self.expire_license()
        self.check_readonly()
