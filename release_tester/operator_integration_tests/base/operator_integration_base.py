"""base class for operator integration test suites"""

# pylint: disable=import-error
import semver
import secrets

from arangodb.async_client import CliExecutionException
from arangodb.installers import create_config_installer_set
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import run_after_suite
from test_suites_core.cli_test_suite import CliStartedTestSuite, CliTestSuiteParameters
from tools.killall import kill_all_processes

from operator_integration_tests.helpers.rbac_helper import RBACHelper

JWT_DIR = "jwt"
OPERATOR_DIR = "operator"


class OperatorIntegrationBaseTestSuite(CliStartedTestSuite):
    """base class for operator integration test suites"""

    # pylint: disable=too-many-instance-attributes disable=too-many-boolean-expressions
    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        eligible, reason = self._check_versions_eligible()
        if not eligible:
            self.__class__.is_disabled = True
            # pylint: disable=no-member
            self.__class__.disable_reasons.append(reason)
        self.sub_suite_name = self.__doc__ if self.__doc__ else self.__class__.__name__
        self.installer_set = create_config_installer_set(
            versions=[self.old_version, self.new_version] if self.old_version else [self.new_version],
            base_config=self.base_cfg,
            deployment_mode="all",
            run_properties=self.run_props,
            force_manual_upgrade=False,
        )
        self.installer = self.installer_set[0][1]
        self.starter = None
        self.instance = None
        self.runner = None
        self.passvoid = ""
        self.publicip = self.base_cfg.publicip
        self.arangod_url = f"http://{self.publicip}:8529"
        self.parent_test_suite_name = (
            f"Operator integration test suite: ArangoDB v. {str(self.new_version)} ({self.installer.installer_type})"
        )
        # create JWT secret and operator binaries folders
        self.jwt_dir = self.base_cfg.test_data_dir / JWT_DIR
        self.jwt_dir.mkdir(parents=False, exist_ok=True)
        self.create_jwt_secret()
        self.operator_dir = self.base_cfg.test_data_dir / OPERATOR_DIR
        self.operator_dir.mkdir(parents=False, exist_ok=True)
        self.rbh = RBACHelper(self.operator_dir, self.jwt_dir)

    def _check_versions_eligible(self):
        """Check that test suite is compatible with ArangoDB versions that are being tested.
        If not, disable test suite.
        """
        if self.new_version is not None and semver.VersionInfo.parse(self.new_version) <= semver.VersionInfo.parse(
            "3.12.11"
        ):
            return False, "This test suite is only applicable to versions 3.12.11 and higher"
        else:
            return True, None

    def init_child_class(self, child_class):
        """initialize the child class"""
        return child_class(self.params)

    def create_jwt_secret(self):
        with open(f"{self.jwt_dir}/-", "w") as f:
            f.write(secrets.token_hex(32))

    @run_after_suite
    def teardown_suite(self):
        """License manager base test suite: teardown"""
        if self.runner:
            self.runner.starter_shutdown()
        kill_all_processes()
