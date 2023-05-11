"""License manager tests: leader-follower"""
import json

# pylint: disable=import-error
from arangodb.installers import RunProperties
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner, RunnerType
from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import run_before_suite


class LicenseManagerLeaderFollowerBaseTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: leader-follower"""

    def get_default_instance_type(self):
        """get the instance type we should communicate with"""
        return InstanceType.SINGLE

    @run_before_suite
    def startup(self):
        """clean up the system before running license manager tests on a leader-follower setup"""
        self.start_leader_follower()

    # pylint: disable=consider-using-with
    def get_server_id(self):
        """read server id from data dir"""
        datadir = self.starter.all_instances[0].basedir / "data"
        server_file_content = json.load(open(datadir / "SERVER", encoding="utf-8"))
        server_id = server_file_content["serverId"]
        return server_id

    # pylint: disable=redefined-builtin disable=arguments-differ
    def set_license(self, license, starter_instance=None):
        """set new license"""
        if not starter_instance:
            starter_instance = self.starter
        datadir = starter_instance.all_instances[0].basedir / "data"
        with open(datadir / ".license", "w", encoding="utf-8") as license_file:
            license_file.truncate()
            license_file.write(license)
        starter_instance.restart_arangods()
        self.wait()

    @step
    def start_leader_follower(self):
        """start a leader-follower setup"""
        # pylint: disable=attribute-defined-outside-init
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
