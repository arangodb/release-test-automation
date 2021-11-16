from pathlib import Path

from arangodb.installers import create_config_installer_set
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite


class BasePackageInstallationTestSuite(BaseTestSuite):
    def __init__(
        self,
        old_version,
        new_version,
        verbose,
        package_dir,
        alluredir,
        clean_alluredir,
        enterprise,
        zip_package,
        interactive,
    ):
        super().__init__()
        self.results_dir = alluredir
        self.clean_allure_dir = clean_alluredir
        self.enterprise = enterprise
        self.zip_package = zip_package
        self.new_version = new_version
        self.enc_at_rest = None
        self.old_version = old_version
        self.parent_test_suite_name = None
        self.auto_generate_parent_test_suite_name = False
        self.suite_name = None
        self.runner_type = None
        self.installer_type = None
        self.ssl = None
        self.use_subsuite = False
        self.installers = {}
        self.installers["community"] = create_config_installer_set(
            versions=[old_version, new_version],
            verbose=verbose,
            enterprise=False,
            encryption_at_rest=False,
            zip_package=zip_package,
            package_dir=Path(package_dir),
            test_dir=None,
            mode="all",
            publicip="127.0.0.1",
            interactive=interactive,
            stress_upgrade=False,
        )
        self.installers["enterprise"] = create_config_installer_set(
            versions=[old_version, new_version],
            verbose=verbose,
            enterprise=True,
            encryption_at_rest=False,
            zip_package=zip_package,
            package_dir=Path(package_dir),
            test_dir=None,
            mode="all",
            publicip="127.0.0.1",
            interactive=interactive,
            stress_upgrade=False,
        )
        self.old_inst_e = self.installers["enterprise"][0][1]
        self.new_inst_e = self.installers["enterprise"][1][1]
        self.old_inst_c = self.installers["community"][0][1]
        self.new_inst_c = self.installers["community"][1][1]

    @step
    def teardown_testcase(self):
        """uninstall all packages"""
        installers = [self.old_inst_e, self.new_inst_e, self.old_inst_c, self.new_inst_c]
        for installer in installers:
            if installer.cfg.debug_package_is_installed:
                installer.un_install_debug_package()
        for installer in installers:
            if installer.cfg.client_package_is_installed:
                installer.un_install_client_package()
        for installer in installers:
            if installer.cfg.server_package_is_installed:
                installer.un_install_server_package()