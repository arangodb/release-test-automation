"""License manager tests: leader-follower"""

# pylint: disable=import-error
from arangodb.async_client import CliExecutionException
from license_manager_tests.base.leader_follower_base import LicenseManagerLeaderFollowerBaseTestSuite
from license_manager_tests.upgrade.license_manager_upgrade_base_test_suite import LicenseManagerUpgradeBaseTestSuite
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import testcase


class LicenseManagerLeaderFollowerUpgradeTestSuite(
    LicenseManagerLeaderFollowerBaseTestSuite, LicenseManagerUpgradeBaseTestSuite
):
    """License manager tests: upgrade leader-follower"""

    @step
    def upgrade_leader_follower(self):
        """upgrade a leader-follower setup"""
        self.new_installer.calculate_package_names()
        self.new_installer.upgrade_server_package(self.old_installer)
        self.new_installer.output_arangod_version()
        self.new_installer.stop_service()
        self.runner.cfg.set_directories(self.new_installer.cfg)
        self.runner.new_cfg.set_directories(self.new_installer.cfg)
        self.runner.upgrade_arangod_version()  # make sure to pass new version
        self.old_installer.un_install_server_package_for_upgrade()

    @testcase
    def upgrade_when_license_is_expired(self):
        """Check that upgrade can be performed with expired license"""
        with step("Create test data"):
            self.runner.leader_starter_instance.arangosh.run_command(
                ("create collection", 'db._create("upgrade_when_license_is_expired");'), True, expect_to_fail=False
            )
            self.runner.leader_starter_instance.arangosh.run_command(
                (
                    "create documents",
                    'for(let i = 0; i < 100; ++i){ db.upgrade_when_license_is_expired.save({"id": i, "a": Math.random(1)})};',
                ),
                True,
                expect_to_fail=False,
            )
        self.expire_license()
        self.upgrade_leader_follower()
        with step("check that data is present after the upgrade"):
            try:
                self.runner.leader_starter_instance.arangosh.run_command(
                    (
                        "check that data is present",
                        'console.assert(db._query("for d in upgrade_when_license_is_expired collect with count into l return l==100").data.result[0])',
                    ),
                    True,
                    expect_to_fail=False,
                )
            except CliExecutionException as ex:
                raise Exception("Can't read data that was created before the upgrade.") from ex
        self.check_readonly()