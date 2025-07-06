"""base class for license manager test suites"""

from time import sleep

# pylint: disable=import-error
import semver

from arangodb.instance import InstanceType
from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step


# pylint: disable=abstract-method
class LicenseManagerNewBaseTestSuite(LicenseManagerBaseTestSuite):
    """base class for license manager test suites"""

    def _check_versions_eligible(self):
        """Check that test suite is compatible with ArangoDB versions that are being tested.
        If not, disable test suite.
        """
        # pylint: disable=no-else-return
        if self.new_version is not None and semver.VersionInfo.parse(self.new_version) <= semver.VersionInfo.parse(
            "3.12.5"
        ):
            return False, "This test suite is only applicable to versions above 3.12.5"
        else:
            return True, None

    @staticmethod
    def sleep(seconds: int = 60):
        """sleep"""
        with step(f"sleep for {seconds} seconds"):
            sleep(seconds)

    @step
    def create_data(self, size_mb: int = 30, repl_factor: int = 3, number_of_shards: int = 30):
        """create data"""
        script = """
            db._create("license_test_collection", {
                numberOfShards: %d,
                replicationFactor: %d,
                writeConcern: %d,
                waitForSync: true
            });

            function createRandomString(length) {
                const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
                let result = "";
                for (let i = 0; i < length; i++) {
                    result += chars.charAt(Math.floor(Math.random() * chars.length));
                }
                return result;
            };
            for (i = 0; i < %d; ++i) {
                db.license_test_collection.save({
                    i,
                    text: createRandomString(1024 * 1024)
                })
            };
        """ % (
            number_of_shards,
            repl_factor,
            repl_factor,
            size_mb,
        )

        self.starter.arangosh.run_command(("create data", script))

    @step
    def check_that_disk_usage_limit_is_reached(self):
        """check that disk usage limit is reached"""
        assert self.get_license()["diskUsage"]["limitReached"]

    @step
    def check_that_disk_usage_limit_is_not_reached(self):
        """check that disk usage limit is NOT reached"""
        assert not self.get_license()["diskUsage"]["limitReached"]

    @step
    def check_disk_usage_status(self, expected="good"):
        """check disk usage status"""
        actual = self.get_license()["diskUsage"]["status"]
        assert actual == expected, f"Wrong disk usage status: ${actual}. Expected: ${expected}"

    @step
    def check_logfiles_contain(self, text: str, instance_type: InstanceType):
        """check that arangod log files contain text"""
        for starter in self.runner.starter_instances:
            for logfile in [
                arangod.logfile for arangod in starter.all_instances if arangod.instance_type == instance_type
            ]:
                text_found = False
                with open(logfile, "r", encoding="utf-8") as file:
                    for line in file:
                        if text in line:
                            text_found = True
                            break
                # pylint: disable=no-else-return disable=no-else-continue
                if text_found:
                    continue
                else:
                    raise Exception(f"Log file {str(logfile)} doesn't contain expected text: {text}")

    @step
    def check_logfiles_do_not_contain(self, text: str, instance_type: InstanceType):
        """check that arangod log files do NOT contain expected text"""
        for starter in self.runner.starter_instances:
            for logfile in [
                arangod.logfile for arangod in starter.all_instances if arangod.instance_type == instance_type
            ]:
                with open(logfile, "r", encoding="utf-8") as file:
                    for line in file:
                        if text in line:
                            raise Exception(f"Log file {str(logfile)} contains unexpected text: {text}")

    @step
    def check_shutdown(self):
        """[SKIPPED] check that deployment has shut down"""
        # we do not actually check for shutdown,
        # because it happens after a timeout of 10 mninutes, that cannot be parametrized
        # this would make tests slow
