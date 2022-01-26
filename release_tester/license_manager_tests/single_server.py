"""License manager tests: single server"""
import json
import shutil
from pathlib import Path
# pylint: disable=E0401
from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager
from license_manager_tests.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import testcase, run_before_suite, run_after_suite


class LicenseManagerSingleServerTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: single server"""
    # pylint: disable=W0102
    def __init__(self, new_version, installer_base_config, child_classes=[]):
        super().__init__(
            new_version,
            installer_base_config,
            child_classes,
        )
        self.short_name = "SingleServer"

    @run_before_suite
    def start(self):
        """clean up the system before running tests"""
        self.cleanup()
        self.start_single_server()

    @run_after_suite
    def shutdown(self):
        """shutdown instance"""
        self.starter.terminate_instance()

    def get_server_id(self):
        """read server ID from data directory"""
        datadir = self.starter.all_instances[0].basedir / "data"
        server_file_content = json.load(open(datadir / "SERVER"))
        server_id = server_file_content["serverId"]
        return server_id

    # pylint: disable=W0622
    def set_license(self, license):
        """set new license"""
        datadir = self.starter.all_instances[0].basedir / "data"
        with open(datadir / ".license", "w") as license_file:
            license_file.truncate()
            license_file.write(license)
        self.starter.terminate_instance()
        self.starter.respawn_instance()

    def cleanup(self):
        """remove all directories created by previous run of this test"""
        testdir = self.base_cfg.test_data_dir / self.short_name
        if testdir.exists():
            shutil.rmtree(testdir)

    @step
    def start_single_server(self):
        """start a single server setup"""
        # pylint: disable=W0201
        self.starter = StarterManager(
            basecfg=self.installer.cfg,
            install_prefix=Path(self.short_name),
            instance_prefix="single",
            expect_instances=[InstanceType.SINGLE],
            mode="single",
            jwt_str="single",
        )
        self.starter.run_starter()
        self.starter.detect_instances()
        self.starter.detect_instance_pids()
        self.starter.set_passvoid(self.passvoid)
        self.instance = self.starter.instance

    @testcase
    def clean_install_temp_license(self):
        """Check that server gets a 60-minute license after installation on a clean system"""
        self.check_that_license_is_not_expired(50 * 60)

    @testcase
    def goto_read_only_mode_when_license_expired(self):
        """Check that system goes to read-only mode when license is expired"""
        self.expire_license()
        self.check_readonly()
