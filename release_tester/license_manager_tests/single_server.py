import json

import requests

from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager
from license_manager_tests.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import testcase


class LicenseManagerSingleServerTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: single server"""

    @step
    def tear_down_test_suite(self):
        """clean up the system after running tests"""
        self.starter.terminate_instance()

    def get_server_id(self):
        datadir = self.starter.all_instances[0].basedir / "data"
        server_file_content = json.load(open(datadir / "SERVER"))
        server_id = server_file_content["serverId"]
        return server_id

    def set_license(self, license):
        datadir = self.starter.all_instances[0].basedir / "data"
        with open(datadir / ".license", "w") as license_file:
            license_file.truncate()
            license_file.write(license)
        self.starter.terminate_instance()
        self.starter.respawn_instance()

    @step
    def start_single_server(self):
        self.starter = StarterManager(
            basecfg=self.installer.cfg,
            install_prefix=self.installer.cfg.install_prefix,
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
        self.start_single_server()
        self.check_that_license_is_not_expired(50 * 60)

    @testcase
    def goto_read_only_mode_when_license_expired(self):
        """Check that system goes to read-only mode when license is expired"""
        self.expire_license()
        self.check_readonly()
