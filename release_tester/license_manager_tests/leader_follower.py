import json

from arangodb.async_client import CliExecutionException
from arangodb.installers import RunProperties
from arangodb.starter.deployments import make_runner, RunnerType
from license_manager_tests.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import testcase


class LicenseManagerLeaderFollowerTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: leader-follower"""

    @step
    def setup_test_suite(self):
        """clean up the system before running tests"""
        self.start_leader_follower()

    def get_server_id(self):
        datadir = self.starter.all_instances[0].basedir / "data"
        server_file_content = json.load(open(datadir / "SERVER"))
        server_id = server_file_content["serverId"]
        return server_id

    def set_license(self, license, starter_instance=None):
        if not starter_instance:
            starter_instance = self.starter
        datadir = starter_instance.all_instances[0].basedir / "data"
        with open(datadir / ".license", "w") as license_file:
            license_file.truncate()
            license_file.write(license)
        starter_instance.terminate_instance()
        starter_instance.respawn_instance()

    @step
    def start_leader_follower(self):
        self.runner = make_runner(
            runner_type=RunnerType.LEADER_FOLLOWER,
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
        self.runner.leader_starter_instance.detect_arangosh_instances()
        self.runner.follower_starter_instance.detect_arangosh_instances()
        self.starter = self.runner.leader_starter_instance

    @testcase
    def clean_install_temp_license(self):
        """Check that server gets a 60-minute license after installation on a clean system"""
        self.check_that_license_is_not_expired(50 * 60)

    @testcase
    def goto_read_only_mode_when_license_expired(self):
        """Check that system goes to read-only mode when license is expired on leader"""
        self.expire_license()
        self.check_readonly()

    @testcase(disable=True)
    def expire_license_on_follower(self):
        """Check that follower goes to read-only mode when license is expired"""
        with step("Expire license on follower"):
            self.starter = self.runner.follower_starter_instance
            self.expire_license()
            self.starter = self.runner.leader_starter_instance
        with step("Create collection on leader"):
            self.runner.leader_starter_instance.arangosh.run_command(
                ("create collection", 'db._create("checkExpireLicenseOnFollower");'), True, expect_to_fail=False
            )
        with step("Check that collection wasn't replicated to follower"):
            try:
                self.runner.follower_starter_instance.arangosh.run_command(
                    ("try to read collection", "db._query('FOR doc IN checkExpireLicenseOnFollower RETURN doc');"),
                    True,
                    expect_to_fail=True,
                )
            except CliExecutionException as ex:
                raise Exception(
                    "Collection was replicated to follower after license expiry. Follower must be in read-only mode!"
                ) from ex
