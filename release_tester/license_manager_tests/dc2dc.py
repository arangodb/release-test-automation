"""License manager tests: DC2DC"""

# pylint: disable=import-error
from arangodb.async_client import CliExecutionException
from license_manager_tests.base.dc2dc_base import LicenseManagerDc2DcBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import testcase, disable


class LicenseManagerDc2DcTestSuite(LicenseManagerDc2DcBaseTestSuite):
    """License manager tests: DC2DC"""

    @testcase
    def clean_install_temp_license(self):
        """Check that server gets a 60-minute license after installation on a clean system"""
        self.check_that_license_is_not_expired(50 * 60)

    @testcase
    def goto_read_only_mode_when_license_expired(self):
        """Check that system goes to read-only mode when license is expired"""
        self.expire_license()
        self.check_readonly()

    @disable
    @testcase
    def expire_license_on_follower_cluster(self):
        """Check that follower cluster goes to read-only mode when license is expired"""
        with step("Expire license on follower"):
            # pylint: disable=attribute-defined-outside-init
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
