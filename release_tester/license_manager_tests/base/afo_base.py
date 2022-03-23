"""License manager tests: active failover"""
import requests

# pylint: disable=import-error
from arangodb.installers import RunProperties
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner, RunnerType
from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import run_before_suite


class LicenseManagerAfoBaseTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: active failover"""

    def get_default_instance_type(self):
        """get the instance type we should communicate with"""
        return InstanceType.RESILIENT_SINGLE

    @run_before_suite
    def startup(self):
        """prepare test environment to run license manager tests on AFO setup"""
        self.start_afo()

    @step
    def start_afo(self):
        """start an AFO setup"""
        # pylint: disable=attribute-defined-outside-init
        self.runner = make_runner(
            runner_type=RunnerType.ACTIVE_FAILOVER,
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
        self.starter = self.runner.leader

    def get_server_id(self):
        """read server ids from agency"""
        agents = self.get_agents()
        agent_ids = []
        for agent in agents:
            agent_ids.append((agent.basedir / "data" / "UUID").read_text())
        agent_ids.sort()
        return "".join(agent_ids)

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
