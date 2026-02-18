"""License manager tests: single server"""

import semver

from arangodb.installers import RunProperties
from arangodb.installers.depvar import RunnerType
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner
from arangodb.starter.deployments.none import NoStarter
from license_manager_tests.base.license_manager_new_base_test_suite import LicenseManagerNewBaseTestSuite
from license_manager_tests.base.single_server_base import LicenseManagerSingleServerBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import testcase, TestMustBeSkipped, disable

# pylint: disable=import-error
from test_suites_core.cli_test_suite import CliTestSuiteParameters


class LicenseManagerSingleServerNewTestSuite(LicenseManagerNewBaseTestSuite, LicenseManagerSingleServerBaseTestSuite):
    """License manager tests: single server"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.suite_name = "New license manager tests(100GB limit): Clean install"

    @step
    def start_single_server(self):
        """start a single server setup"""
        self.runner = make_runner(
            runner_type=RunnerType.SINGLE,
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
        if isinstance(self.runner, NoStarter):
            raise TestMustBeSkipped(self.runner.msg)
        self.runner.starter_prepare_env(
            more_opts=[
                # set disk usage limit to 30MB
                "--args.all.server.license-disk-usage-limit=31457280",
                # set disk usage and license update intervals to minimum
                "--args.all.server.license-disk-usage-update-interval=1",
                "--args.all.server.license-check-interval=1",
                # set grace periods to 10 seconds
                "--args.all.server.license-disk-usage-grace-period-readonly=10",
                "--args.all.server.license-disk-usage-grace-period-shutdown=10",
            ]
        )
        self.runner.starter_run()
        self.runner.finish_setup()
        self.runner.starter_instance.detect_arangosh_instances(self.runner.starter_instance, self.runner.cfg.version)
        self.starter = self.runner.starter_instance

    @step
    def recreate_deployment(self):
        """recreate deployment"""
        self.runner.starter_shutdown()
        self.runner.cleanup()
        self.start_single_server()

    @testcase
    def test_01_clean_install_no_license(self):
        """Check that server without a license is fully functional when disk usage limit is not reached"""
        self.check_that_disk_usage_limit_is_not_reached()
        self.check_disk_usage_status()
        self.check_not_readonly()

    @testcase
    def test_02_disk_usage_limit_reached_no_license(self):
        """Check that deployment goes into read-only mode when disk usage limit is reached"""
        self.create_data()
        self.sleep(2)
        self.check_that_disk_usage_limit_is_reached()
        self.check_logfiles_contain("d72fc", InstanceType.SINGLE)
        self.check_logfiles_contain("disk usage exceeded the free limit", InstanceType.SINGLE)
        self.sleep(10)
        self.check_readonly()
        old_version = semver.VersionInfo.parse("3.12.7-99")
        if (
            self.new_version is not None
            and semver.VersionInfo.parse(self.new_version) < old_version
            ):
            self.check_logfiles_contain("f4b90", InstanceType.COORDINATOR)
        else:
            self.check_logfiles_contain("f4b91", InstanceType.COORDINATOR)
        self.check_logfiles_contain("Operation has been restricted to read-only mode", InstanceType.SINGLE)
        self.sleep(10)
        self.check_shutdown()
        self.check_logfiles_contain("d73f5", InstanceType.SINGLE)
        self.check_logfiles_contain("Server will shut down in 10 minutes", InstanceType.SINGLE)

    @disable("re-enable when license generator is compatible with v. 3.12+")
    @testcase
    def test_03_disk_usage_limit_reached_valid_license(self):
        """When valid license is applied, reaching disk usage limit must not trigger read-only mode"""
        self.recreate_deployment()
        self.set_valid_license()
        self.create_data()
        self.sleep(11)
        self.check_not_readonly()
        self.check_logfiles_do_not_contain("d72fc", InstanceType.SINGLE)
        self.check_logfiles_do_not_contain("disk usage exceeded the free limit", InstanceType.SINGLE)
        old_version = semver.VersionInfo.parse("3.12.7-99")
        if (
            self.new_version is not None
            and semver.VersionInfo.parse(self.new_version) < old_version
            ):
            self.check_logfiles_contain("f4b90", InstanceType.COORDINATOR)
        else:
            self.check_logfiles_contain("f4b91", InstanceType.COORDINATOR)
        self.check_logfiles_do_not_contain("Operation has been restricted to read-only mode", InstanceType.SINGLE)
        self.sleep(11)
        self.check_logfiles_do_not_contain("d73f5", InstanceType.SINGLE)
        self.check_logfiles_do_not_contain("Server will shut down in 10 minutes", InstanceType.SINGLE)

    @disable("re-enable when license generator is compatible with v. 3.12+")
    @testcase
    def test_04_goto_read_only_mode_when_license_expired(self):
        """Check that system goes to read-only mode when license is expired"""
        self.recreate_deployment()
        self.set_valid_license()
        self.create_data()
        self.expire_license()
        self.sleep(12)
        self.check_readonly()
