"""License manager tests: single server"""
import json
import shutil
from pathlib import Path

# pylint: disable=import-error
from allure_commons._allure import attach

from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager
from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import testcase, run_before_suite, run_after_suite, collect_crash_data
from tools.killall import kill_all_processes


class LicenseManagerSingleServerTestSuite(LicenseManagerBaseTestSuite):
    """License manager tests: single server"""

    # pylint: disable=dangerous-default-value
    def __init__(self, new_version, installer_base_config, child_classes=[]):
        super().__init__(
            new_version,
            installer_base_config,
            child_classes,
        )
        self.short_name = "SingleServer"

    def get_default_instance_type(self):
        """get the instance type we should communicate with"""
        return InstanceType.SINGLE

    @collect_crash_data
    def save_data_dir(self):
        """save data dir and logs in case a test failed"""
        kill_all_processes()
        if self.starter.basedir.exists():
            archive = shutil.make_archive(
                f"LicenseManagerSingleServerTestSuite(v. {self.base_cfg.version})", "bztar", self.starter.basedir
            )
            attach.file(archive, "test dir archive", "application/x-bzip2", "tar.bz2")
        else:
            print("test basedir doesn't exist, won't create report tar")

    @run_before_suite
    def start(self):
        """clean up the system before running license manager tests on a single server setup"""
        self.cleanup()
        self.start_single_server()

    @run_after_suite
    def teardown_suite(self):
        """Teardown suite environment: single server"""
        self.starter.terminate_instance()
        kill_all_processes()
        self.installer.cleanup_system()

    def get_server_id(self):
        """read server ID from data directory"""
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
        self.starter.respawn_instance()

    def cleanup(self):
        """remove all directories created by previous run of this test"""
        testdir = self.base_cfg.test_data_dir / self.short_name
        if testdir.exists():
            shutil.rmtree(testdir)

    @step
    def start_single_server(self):
        """start a single server setup"""
        # pylint: disable=attribute-defined-outside-init
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
