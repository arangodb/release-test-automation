from pathlib import Path

from allure_commons._allure import attach

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
            ssl=False,
            hot_backup="disabled",
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
            ssl=False,
            hot_backup="disabled",
        )
        self.old_inst_e = self.installers["enterprise"][0][1]
        self.new_inst_e = self.installers["enterprise"][1][1]
        self.old_inst_c = self.installers["community"][0][1]
        self.new_inst_c = self.installers["community"][1][1]

    @step
    def setup_test_suite(self):
        """clean up the system before running tests"""
        self.uninstall_everything()

    @step
    def tear_down_test_suite(self):
        """clean up the system after running tests"""
        self.uninstall_everything()

    @step
    def teardown_testcase(self):
        """clean up after test case"""
        self.uninstall_everything()

    @step
    def uninstall_everything(self):
        """uninstall all packages"""
        self.new_inst_c.uninstall_everything()
        for installer in [self.old_inst_e, self.new_inst_e, self.old_inst_c, self.new_inst_c]:
            installer.cleanup_system()
            installer.cfg.server_package_is_installed = False
            installer.cfg.debug_package_is_installed = False
            installer.cfg.client_package_is_installed = False

    def add_crash_data_to_report(self):
        inst = self.installers["enterprise"][0][1]
        if inst.instance and inst.instance.logfile.exists():
            log = open(inst.instance.logfile, "r").read()
            attach(log, "Log file " + str(inst.instance.logfile))
