"""License manager tests: single server"""
import json

# pylint: disable=import-error
from arangodb.installers import RunProperties
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner, RunnerType
from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import run_before_suite


class LicenseManagerSingleServerBaseTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: single server"""

    def get_default_instance_type(self):
        """get the instance type we should communicate with"""
        return InstanceType.SINGLE

    @run_before_suite
    def start(self):
        """start a single server setup before running tests"""
        self.start_single_server()

    @step
    def start_single_server(self):
        """start a single server setup"""
        self.runner = make_runner(
            runner_type=RunnerType.SINGLE,
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
        self.runner.starter_instance.detect_arangosh_instances()
        self.starter = self.runner.starter_instance

    def get_server_id(self):
        """read server id from data dir"""
        datadir = self.starter.all_instances[0].basedir / "data"
        server_file_content = json.load(open(datadir / "SERVER"))
        server_id = server_file_content["serverId"]
        return server_id

    # pylint: disable=redefined-builtin
    def set_license(self, license):
        """set new license"""
        datadir = self.starter.all_instances[0].basedir / "data"
        with open(datadir / ".license", "w") as license_file:
            license_file.truncate()
            license_file.write(license)
        self.starter.terminate_instance()
        self.starter.respawn_instance()