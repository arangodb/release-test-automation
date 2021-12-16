#!/usr/bin/env python3
"""base class for package conflict checking"""
import shutil
from pathlib import Path

from allure_commons._allure import attach

from arangodb.installers import create_config_installer_set, RunProperties
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite


class BasePackageInstallationTestSuite(BaseTestSuite):
    """base class for package conflict checking"""
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
        self.use_subsuite = False
        self.installers = {}
        self.installers["community"] = create_config_installer_set(
            versions=[old_version, new_version],
            verbose=verbose,
            zip_package=zip_package,
            package_dir=Path(package_dir),
            test_dir=None,
            mode="all",
            publicip="127.0.0.1",
            interactive=interactive,
            stress_upgrade=False,
            hot_backup="disabled",
            run_properties=RunProperties(enterprise=False,
                                         encryption_at_rest=False,
                                         ssl=False)
        )
        self.installers["enterprise"] = create_config_installer_set(
            versions=[old_version, new_version],
            verbose=verbose,
            zip_package=zip_package,
            package_dir=Path(package_dir),
            test_dir=None,
            mode="all",
            publicip="127.0.0.1",
            interactive=interactive,
            stress_upgrade=False,
            hot_backup="disabled",
            run_properties=RunProperties(enterprise=True,
                                         encryption_at_rest=False,
                                         ssl=False)
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
        self.save_log_file()
        self.save_data_dir()

    def save_log_file(self):
        """upload a logfile into the report."""
        inst = self.installers["enterprise"][0][1]
        if inst.instance and inst.instance.logfile.exists():
            log = open(inst.instance.logfile, "r").read()
            attach(log, "Log file " + str(inst.instance.logfile))

    def save_data_dir(self):
        """upload a system database directory into the report"""
        inst = self.installers["enterprise"][0][1]
        data_dir = inst.cfg.dbdir
        if data_dir.exists():
            archive = shutil.make_archive("datadir", "bztar", data_dir, data_dir)
            attach.file(archive, "data directory archive", "application/x-bzip2", "tar.bz2")
