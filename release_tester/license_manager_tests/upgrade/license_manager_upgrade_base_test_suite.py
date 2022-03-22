"""base class for license manager test suites that require upgrading arangodbs"""

# pylint: disable=import-error
from arangodb.installers import create_config_installer_set, RunProperties
from license_manager_tests.base.license_manager_base_test_suite import LicenseManagerBaseTestSuite
from selenium_ui_test.test_suites.base_test_suite import run_after_suite, run_before_suite

try:
    from tools.external_helpers.license_generator.license_generator import create_license

    EXTERNAL_HELPERS_LOADED = True
except ModuleNotFoundError as exc:
    print("External helpers not found. License manager tests will not run.")
    EXTERNAL_HELPERS_LOADED = False


class LicenseManagerUpgradeBaseTestSuite(LicenseManagerBaseTestSuite):
    """base class for license manager test suites that require upgrading arangodb"""

    # pylint: disable=too-many-instance-attributes disable=dangerous-default-value
    def __init__(
        self,
        old_version,
        new_version,
        installer_base_config,
        child_classes=[],
    ):
        package_type = ".tar.gz" if installer_base_config.zip_package else ".deb/.rpm/NSIS"
        self.suite_name = f"Licence manager test suite: ArangoDB v. {str(new_version)} ({package_type})"
        self.auto_generate_parent_test_suite_name = False
        super().__init__(new_version, installer_base_config, child_classes)
        self.old_version = old_version
        run_props = RunProperties(
            enterprise=True,
            encryption_at_rest=False,
            ssl=False,
        )
        versions = [self.old_version, self.new_version]
        self.installer_set = create_config_installer_set(
            versions=versions, base_config=self.base_cfg, deployment_mode="all", run_properties=run_props
        )
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
        self.runner.starter_shutdown()
        self.new_installer.un_install_server_package()

    @run_before_suite
    def install_package(self):
        """clean up the system before running the license manager test suites"""
        self.old_installer.install_server_package()
        self.old_installer.stop_service()
