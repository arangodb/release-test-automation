"""base class for license manager test suites that require upgrading arangodbs"""

# pylint: disable=import-error
from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import run_after_suite, run_before_suite
from test_suites_core.cli_test_suite import CliTestSuiteParameters

try:
    from tools.external_helpers.license_generator.license_generator import create_license

    EXTERNAL_HELPERS_LOADED = True
except ModuleNotFoundError as exc:
    print("External helpers not found. License manager tests will not run.")
    EXTERNAL_HELPERS_LOADED = False


class LicenseManagerUpgradeBaseTestSuite(LicenseManagerBaseTestSuite):
    """base class for license manager test suites that require upgrading arangodb"""

    # pylint: disable=too-many-instance-attributes disable=dangerous-default-value
    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.suite_name = "License manager tests: Upgrade"
        versions = [self.old_version, self.new_version]
        self.old_installer = self.installer_set[0][1]
        self.new_installer = self.installer_set[1][1]
        self.installer = self.new_installer

    # pylint: disable=no-self-use
    def init_child_class(self, child_class):
        """initialise the child class"""
        return child_class(self.new_version, self.base_cfg, self.old_version)

    @run_after_suite
    def teardown(self):
        """teardown test suite"""
        if self.new_installer.cfg.server_package_is_installed:
            self.new_installer.un_install_server_package()
        if self.old_installer.cfg.server_package_is_installed:
            self.old_installer.un_install_server_package()
        self.old_installer.cleanup_system()

    @run_before_suite
    def install_package(self):
        """clean up the system before running the license manager test suites"""
        self.old_installer.install_server_package()
        self.old_installer.stop_service()

    @step
    def upgrade(self):
        """upgrade a deployment"""
        self.new_installer.calculate_package_names()
        self.new_installer.upgrade_server_package(self.old_installer)
        self.new_installer.output_arangod_version()
        self.new_installer.stop_service()
        self.runner.cfg.set_directories(self.new_installer.cfg)
        self.runner.new_cfg.set_directories(self.new_installer.cfg)
        self.runner.upgrade_arangod_version()  # make sure to pass new version
        self.old_installer.un_install_server_package_for_upgrade()
