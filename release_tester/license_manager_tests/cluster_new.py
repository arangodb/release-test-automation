"""License manager tests: cluster"""

# pylint: disable=import-error
import semver

from arangodb.installers import RunProperties
from arangodb.installers.depvar import RunnerType
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner
from arangodb.starter.deployments.none import NoStarter
from license_manager_tests.base.cluster_base import LicenseManagerClusterBaseTestSuite
from license_manager_tests.base.license_manager_new_base_test_suite import LicenseManagerNewBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import testcase, TestMustBeSkipped
from test_suites_core.cli_test_suite import CliTestSuiteParameters


class LicenseManagerClusterNewTestSuite(LicenseManagerNewBaseTestSuite, LicenseManagerClusterBaseTestSuite):
    """License manager tests: cluster"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.suite_name = "New license manager tests(100GB limit): Clean install"

    @step
    def start_cluster(self):
        """start a cluster setup"""
        # pylint: disable=attribute-defined-outside-init
        self.runner = make_runner(
            runner_type=RunnerType.CLUSTER,
            abort_on_error=False,
            selenium_worker="none",
            selenium_driver_args=[],
            selenium_include_suites=[],
            installer_set=self.installer_set,
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
                # set grace periods to 30 seconds
                "--args.all.server.license-disk-usage-grace-period-readonly=10",
                "--args.all.server.license-disk-usage-grace-period-shutdown=10",
            ]
        )
        self.runner.starter_run()
        self.runner.finish_setup()
        self.starter = self.runner.starter_instances[0]

    @testcase
    def clean_install_no_license(self):
        """Check that server without a license is fully functional when disk usage limit is not reached"""
        self.check_that_disk_usage_limit_is_not_reached()
        self.check_disk_usage_status()
        self.check_not_readonly()

    @testcase
    def disk_usage_limit_reached(self):
        """Check that deployment goes into read-only mode when disk usage limit is reached"""
        self.create_data()
        self.sleep(2)
        self.check_logfiles_contain("d72fc", InstanceType.COORDINATOR)
        self.check_logfiles_contain("disk usage exceeded the free limit", InstanceType.COORDINATOR)
        self.sleep(10)
        self.check_readonly()
        old_version = semver.VersionInfo.parse("3.7.99")
        if (
            self.new_version is not None
            and semver.VersionInfo.parse(self.new_version) < old_version
            ):
            self.check_logfiles_contain("f4b90", InstanceType.COORDINATOR)
        else:
            self.check_logfiles_contain("f4b91", InstanceType.COORDINATOR)
        self.check_logfiles_contain("Operation has been restricted to read-only mode", InstanceType.COORDINATOR)
        self.sleep(10)
        self.check_shutdown()
        self.check_logfiles_contain("d73f5", InstanceType.COORDINATOR)
        self.check_logfiles_contain("Server will shut down in 10 minutes", InstanceType.COORDINATOR)
