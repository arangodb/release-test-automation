"""License manager tests: single server"""
import json

from arangodb.installers import RunProperties
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner, RunnerType
from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import testcase, run_before_suite


# pylint: disable=import-error


class LicenseManagerSingleServerTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: single server"""

    # pylint: disable=dangerous-default-value
    def __init__(self, new_version, installer_base_config):
        super().__init__(
            new_version,
            installer_base_config,
        )
        self.short_name = "SingleServer"

    def get_default_instance_type(self):
        """get the instance type we should communicate with"""
        return InstanceType.SINGLE

    @run_before_suite
    def start(self):
        """start a single server setup before running tests"""
        self.start_single_server()

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
        version = self.new_cfg.version if self.new_cfg != None else self.cfg.version
        self.starter.respawn_instance(version)

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


    @testcase
    def clean_install_temp_license(self):
        """Check that server gets a 60-minute license after installation on a clean system"""
        self.check_that_license_is_not_expired(50 * 60)

    @testcase
    def goto_read_only_mode_when_license_expired(self):
        """Check that system goes to read-only mode when license is expired"""
        self.expire_license()
        self.check_readonly()
