from semver import VersionInfo

from arangodb.installers import OptionGroup, RunProperties, InstallerBaseConfig
from test_suites_core.base_test_suite import BaseTestSuite
from dataclasses import dataclass


@dataclass
class CliTestSuiteParameters(OptionGroup):
    """set of parameters required to run any test suite"""
    new_version: VersionInfo = None
    enterprise: bool = None
    zip_package: bool = None
    src_testing: bool = None
    package_dir: bool = None
    base_cfg: InstallerBaseConfig = None
    old_version: VersionInfo = None



class CliStartedTestSuite(BaseTestSuite):
    """base class for test suites that can be started from CLI"""

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__()
        self.params=params
        self.new_version = params.new_version
        self.old_version = params.old_version
        self.enterprise = params.enterprise
        self.zip_package = params.zip_package
        self.src_testing = params.src_testing
        self.package_dir = params.package_dir
        self.base_cfg = params.base_cfg
        self.run_props = RunProperties(enterprise=self.enterprise)

    def init_child_class(self, child_class):
        """initialise the child class"""
        return child_class(self.params)

