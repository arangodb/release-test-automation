#!/usr/bin/env python3
"""this test suite is intended to perform all checks of the binary files, e.g. stripping, signatures etc."""
import semver

from arangodb.installers import create_config_installer_set
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import parameters, testcase, run_after_each_testcase, run_before_suite
from test_suites_core.cli_test_suite import CliStartedTestSuite, CliTestSuiteParameters


class BinaryComplianceTestSuite(CliStartedTestSuite):
    def __init__(self, params: CliTestSuiteParameters):
        min_version = semver.VersionInfo.parse("3.12.0-nightly")
        super().__init__(params)
        if self.new_version is not None and semver.VersionInfo.parse(self.new_version) < min_version:
            self.__class__.is_disabled = True
            # pylint: disable=no-member
            self.__class__.disable_reasons.append("Test suite is only applicable to versions 3.12 and newer.")
        self.installer_set = create_config_installer_set(
            versions=[self.new_version],
            base_config=self.base_cfg,
            deployment_mode="all",
            run_properties=self.run_props,
            use_auto_certs=False,
        )
        self.installer = self.installer_set[0][1]
        ent = "Enterprise" if self.run_props.enterprise else "Community"
        self.suite_name = f"Binary compliance test suite: ArangoDB v. {str(self.new_version)} ({ent}) ({self.installer.installer_type})"

    @run_after_each_testcase
    def uninstall_everything(self):
        """uninstall all packages"""
        self.installer.un_install_server_package()
        self.installer.un_install_client_package()
        self.installer.uninstall_everything()
        self.installer.cleanup_system()
        self.installer.cfg.server_package_is_installed = False
        self.installer.cfg.client_package_is_installed = False

    @testcase("Check that --version output contains information required by third party libraries(server package)")
    def test_license_info_server_package(self):
        self.installer.install_server_package()
        self.installer.stop_service()
        binaries = [
            file
            for file in self.installer.arango_binaries
            if file.binary_type=="c++" and not (not self.run_props.enterprise and file.enterprise)
        ]
        for bin in binaries:
            with step(f"check {bin.name}"):
                bin.check_license_info()

    @testcase("Check that --version output contains information required by third party libraries(client package)")
    def test_license_info_client_package(self):
        self.installer.install_client_package()
        binaries = [
            file
            for file in self.installer.arango_binaries
            if file.binary_type=="c++" and not (not self.run_props.enterprise and file.enterprise)
        ]
        for bin in binaries:
            with step(f"check {bin.name}"):
                bin.check_license_info()
