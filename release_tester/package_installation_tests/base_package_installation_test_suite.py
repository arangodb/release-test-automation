#!/usr/bin/env python3
"""base class for package conflict checking"""
import shutil

from allure_commons._allure import attach

from arangodb.installers import create_config_installer_set, RunProperties, InstallerBaseConfig
from test_suites_core.base_test_suite import (
    BaseTestSuite,
    run_before_suite,
    run_after_suite,
    run_after_each_testcase,
    collect_crash_data,
)
from test_suites_core.cli_test_suite import CliStartedTestSuite, CliTestSuiteParameters


class BasePackageInstallationTestSuite(CliStartedTestSuite):
    # pylint: disable=too-many-instance-attributes disable=too-many-arguments
    """base class for package conflict checking"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.installers = {}
        versions = [self.old_version, self.new_version]
        self.installers["community"] = create_config_installer_set(
            versions=versions,
            base_config=self.base_cfg,
            deployment_mode="all",
            run_properties=RunProperties(enterprise=False, encryption_at_rest=False, ssl=False),
        )
        self.installers["enterprise"] = create_config_installer_set(
            versions=versions,
            base_config=self.base_cfg,
            deployment_mode="all",
            run_properties=RunProperties(enterprise=True, encryption_at_rest=False, ssl=False),
        )
        self.old_inst_e = self.installers["enterprise"][0][1]
        self.new_inst_e = self.installers["enterprise"][1][1]
        self.old_inst_c = self.installers["community"][0][1]
        self.new_inst_c = self.installers["community"][1][1]

    # pylint: disable=missing-function-docstring
    def is_zip(self):
        return self.zip_package

    # pylint: disable=missing-function-docstring
    def client_package_is_present(self) -> bool:
        return (
            self.old_inst_e.client_package
            and self.new_inst_e.client_package
            and self.old_inst_c.client_package
            and self.new_inst_c.client_package
        )

    # pylint: disable=missing-function-docstring
    def client_package_is_not_present(self) -> bool:
        return not self.client_package_is_present()

    @run_before_suite
    @run_after_suite
    @run_after_each_testcase
    def uninstall_everything(self):
        """uninstall all packages"""
        self.new_inst_c.uninstall_everything()
        for installer in [self.old_inst_e, self.new_inst_e, self.old_inst_c, self.new_inst_c]:
            installer.cleanup_system()
            installer.cfg.server_package_is_installed = False
            installer.cfg.debug_package_is_installed = False
            installer.cfg.client_package_is_installed = False

    @collect_crash_data
    def save_log_file_and_data_dir(self):
        """save log file and data dir"""
        self.save_log_file()
        self.save_data_dir()

    def save_log_file(self):
        """upload a logfile into the report."""
        inst = self.installers["enterprise"][0][1]
        if inst.instance and inst.instance.logfile.exists():
            with open(inst.instance.logfile, "r", encoding="utf8").read() as log:
                attach(log, "Log file " + str(inst.instance.logfile))

    def save_data_dir(self):
        """upload a system database directory into the report"""
        inst = self.installers["enterprise"][0][1]
        data_dir = inst.cfg.dbdir
        if data_dir.exists():
            with shutil.make_archive("datadir", "bztar", data_dir, data_dir) as archive:
                attach.file(archive, "data directory archive", "application/x-bzip2", "tar.bz2")
