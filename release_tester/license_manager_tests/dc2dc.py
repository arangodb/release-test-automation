import json

import requests

from arangodb.async_client import CliExecutionException
from arangodb.installers import RunProperties
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner, RunnerType
from license_manager_tests.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import testcase


class LicenseManagerDc2DcTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: DC2DC"""

    @step
    def start_clusters(self):
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
        self.starter = self.runner.cluster2["instance"]

    def get_server_id(self):
        resp = self.starter.send_request(
            InstanceType.COORDINATOR,
            requests.get,
            "/_api/cluster/agency-dump",
        )
        json_body = json.loads(resp[0].text)
        agent_list = list(json_body["agency"][".agency"]["pool"].keys())
        agent_list.sort()
        return "".join(agent_list)

    def set_license(self, license):
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

    @testcase
    def clean_install_temp_license(self):
        """Check that server gets a 60-minute license after installation on a clean system"""
        self.start_clusters()
        self.check_that_license_is_not_expired(50 * 60)

    @testcase
    def goto_read_only_mode_when_license_expired(self):
        """Check that system goes to read-only mode when license is expired"""
        self.expire_license()
        self.check_readonly()

    @testcase(disable=True)
    def expire_license_on_follower_cluster(self):
        """Check that follower cluster goes to read-only mode when license is expired"""
        with step("Expire license on follower"):
            self.starter = self.runner.cluster1["instance"]
            self.expire_license()
            self.starter = self.runner.cluster2["instance"]
        with step("Create collection on leader cluster"):
            self.starter.arangosh.run_command(
                ("create collection", 'db._create("checkExpireLicenseOnFollower");'), True, expect_to_fail=False
            )
        with step("Check that collection wasn't replicated to follower cluster"):
            try:
                self.runner.cluster1["instance"].arangosh.run_command(
                    ("try to read collection", "db._query('FOR doc IN checkExpireLicenseOnFollower RETURN doc');"),
                    True,
                    expect_to_fail=True,
                )
            except CliExecutionException as ex:
                raise Exception(
                    "Collection was replicated to follower cluster after license expiry. Follower must be in read-only mode!"
                ) from ex
