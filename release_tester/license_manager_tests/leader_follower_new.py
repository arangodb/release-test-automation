"""License manager tests: leader-follower"""

# pylint: disable=import-error
from arangodb.async_client import CliExecutionException
from arangodb.installers import RunProperties
from arangodb.installers.depvar import RunnerType
from arangodb.instance import InstanceType
from arangodb.starter.deployments import make_runner
from arangodb.starter.deployments.none import NoStarter
from license_manager_tests.base.leader_follower_base import LicenseManagerLeaderFollowerBaseTestSuite

from license_manager_tests.base.license_manager_new_base_test_suite import LicenseManagerNewBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import testcase, disable, TestMustBeSkipped
from test_suites_core.cli_test_suite import CliTestSuiteParameters


class LicenseManagerLeaderFollowerNewTestSuite(
    LicenseManagerNewBaseTestSuite, LicenseManagerLeaderFollowerBaseTestSuite
):
    """License manager tests: leader-follower"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.suite_name = "New license manager tests(100GB limit): Clean install"

    @step
    def start_leader_follower(self):
        """start a leader-follower setup"""
        # pylint: disable=attribute-defined-outside-init
        self.runner = make_runner(
            runner_type=RunnerType.LEADER_FOLLOWER,
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
                # set grace periods to 1 minute
                "--args.all.server.license-disk-usage-grace-period-readonly=30",
                "--args.all.server.license-disk-usage-grace-period-shutdown=30",
            ]
        )
        self.runner.starter_run()
        self.runner.finish_setup()
        self.runner.leader_starter_instance.detect_arangosh_instances(
            self.runner.leader_starter_instance.cfg, self.runner.leader_starter_instance.cfg.version
        )
        self.runner.follower_starter_instance.detect_arangosh_instances(
            self.runner.follower_starter_instance.cfg, self.runner.leader_starter_instance.cfg.version
        )
        self.starter = self.runner.leader_starter_instance

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
        self.sleep(10)
        self.check_logfiles_contain("d72fc", InstanceType.SINGLE)
        self.check_logfiles_contain("disk usage exceeded the free limit", InstanceType.SINGLE)
        self.sleep(23)
        self.check_readonly()
        self.check_logfiles_contain("f4b90", InstanceType.SINGLE)
        self.check_logfiles_contain("Operation has been restricted to read-only mode", InstanceType.SINGLE)
        self.sleep(32)
        self.check_shutdown()
        self.check_logfiles_contain("d73f5", InstanceType.SINGLE)
        self.check_logfiles_contain("Server will shut down in 10 minutes", InstanceType.SINGLE)

    @testcase
    def goto_read_only_mode_when_license_expired_on_leader(self):
        """Check that system goes to read-only mode when license is expired"""
        self.expire_license()
        self.check_readonly()

    @disable
    @testcase
    def expire_license_on_follower(self):
        """Check that follower goes to read-only mode when license is expired"""
        with step("Expire license on follower"):
            # pylint: disable=attribute-defined-outside-init
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
