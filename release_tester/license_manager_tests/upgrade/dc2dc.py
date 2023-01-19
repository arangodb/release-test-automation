"""License manager tests: DC2DC"""

# pylint: disable=import-error
from arangodb.async_client import CliExecutionException
from license_manager_tests.base.dc2dc_base import LicenseManagerDc2DcBaseTestSuite
from license_manager_tests.upgrade.license_manager_upgrade_base_test_suite import LicenseManagerUpgradeBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import testcase, disable_for_windows


@disable_for_windows("DC2DC suite is disabled for Windows")
class LicenseManagerDc2DcUpgradeTestSuite(LicenseManagerDc2DcBaseTestSuite, LicenseManagerUpgradeBaseTestSuite):
    """License manager tests: upgrade DC2DC setup"""

    @testcase
    def upgrade_when_license_is_expired(self):
        """Check that upgrade can be performed with expired license"""
        with step("Create test data"):
            self.starter.arangosh.run_command(
                (
                    "create collection",
                    'db._create("upgrade_when_license_is_expired", {"numberOfShards": 30, "replicationFactor": 3, "writeConcern": 3});',
                ),
                True,
                expect_to_fail=False,
            )
            self.starter.arangosh.run_command(
                (
                    "create documents",
                    'for(let i = 0; i < 100; ++i){ db.upgrade_when_license_is_expired.save({"id": i, "a": Math.random(1)})};',
                ),
                True,
                expect_to_fail=False,
            )
        self.expire_license()
        self.upgrade()
        with step("check that data is present after the upgrade"):
            try:
                self.starter.arangosh.run_command(
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
