"""base class for license manager test suites"""

import json
from time import time

import requests

# pylint: disable=import-error
import semver

from arangodb.async_client import CliExecutionException
from arangodb.installers import create_config_installer_set
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import (
    run_after_suite,
    collect_crash_data,
)
from test_suites_core.cli_test_suite import CliStartedTestSuite, CliTestSuiteParameters
from tools.killall import kill_all_processes

try:
    from tools.external_helpers.license_generator.license_generator import create_license

    EXTERNAL_HELPERS_LOADED = True
except ModuleNotFoundError as exc:
    print("External helpers not found. License manager tests will not run.")
    EXTERNAL_HELPERS_LOADED = False


class LicenseManagerBaseTestSuite(CliStartedTestSuite):
    """base class for license manager test suites"""

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
        )
        self.installer = self.installer_set[0][1]
        self.starter = None
        self.instance = None
        self.runner = None
        self.passvoid = "license_manager_tests"
        self.publicip = self.base_cfg.publicip
        self.parent_test_suite_name = (
            f"Licence manager test suite: ArangoDB v. {str(self.new_version)} ({self.installer.installer_type})"
        )

    def _check_versions_eligible(self):
        """Check that test suite is compatible with ArangoDB versions that are being tested."""
        min_version = semver.VersionInfo.parse("3.9.0-nightly")
        max_version = semver.VersionInfo.parse("3.12.4")
        # pylint: disable=no-else-return
        if (
            self.new_version is not None
            and (
                semver.VersionInfo.parse(self.new_version) < min_version
                or semver.VersionInfo.parse(self.new_version) > max_version
            )
        ) or (
            self.old_version is not None
            and (
                semver.VersionInfo.parse(self.old_version) < min_version
                or semver.VersionInfo.parse(self.old_version) > max_version
            )
        ):
            return False, "This test suite is only applicable to versions 3.9.0 to 3.12.4."
        else:
            return True, None

    def init_child_class(self, child_class):
        """initialise the child class"""
        return child_class(self.params)

    @run_after_suite
    def teardown_suite(self):
        """License manager base test suite: teardown"""
        if self.runner:
            self.runner.starter_shutdown()
        kill_all_processes()

    @collect_crash_data
    def save_data_dir(self):
        """save data dir and logs in case a test failed"""
        kill_all_processes()
        self.runner.zip_test_dir()

    @step
    def check_that_license_is_not_expired(self, time_left_threshold=0):
        """check that license is not expired"""
        license_str = self.get_license()
        license_expiry_timestamp = license_str["features"]["expires"]
        time_left = license_expiry_timestamp - time()
        if time_left >= 0:
            message = f"License expires in {time_left} seconds."
        else:
            message = f"License expired {-1 * time_left} seconds ago."
        assert (
            time_left > time_left_threshold
        ), f"{message} Expected time left: more than {time_left_threshold} seconds."

    def get_default_instance_type(self):
        """get the instance type we should communicate with"""
        raise NotImplementedError(f"Default instance type is not set for {type(self)}")

    # pylint: disable=too-many-arguments
    def send_request(self, method, url, data=None, headers=None, timeout=None, instance_type=None):
        """send HTTP request to an instance"""
        if not instance_type:
            instance_type = self.get_default_instance_type()
        resp = self.starter.send_request(
            instance_type=instance_type,
            verb_method=method,
            url=url,
            data=data,
            headers={} if headers is None else headers,
            timeout=timeout,
        )
        return resp

    def get_license(self):
        """read current license via REST API"""
        resp = self.send_request(
            requests.get,
            "/_db/_system/_admin/license",
        )
        license_str = json.loads(resp[0].content)
        return license_str

    def set_license(self, license_str):
        """set new license"""
        raise NotImplementedError(f"Setting license not implemented for {type(self)}")

    @step
    def expire_license(self):
        """expire license"""
        # pylint: disable=assignment-from-no-return
        new_timestamp = str(int(time() - 1))
        server_id = self.get_server_id()
        license_str = create_license(new_timestamp, server_id)
        self.set_license(license_str)

    @step
    def wait(self):
        """wait for the SUT to become responsive"""
        self.runner.tcp_ping_all_nodes()

    # pylint: disable=fixme
    # FIXME: set valid license before each test case
    #    @run_before_each_testcase
    @step
    def set_valid_license(self):
        """set valid license"""
        new_timestamp = str(int(time() + 24 * 60 * 60))
        # pylint: disable=assignment-from-no-return
        server_id = self.get_server_id()
        license_str = create_license(new_timestamp, server_id)
        self.set_license(license_str)

    @step
    def check_readonly(self):
        """check that system is in read-only mode"""
        try:
            result = self.starter.arangosh.run_command(
                ("try to create collection", 'db._create("checkReadOnlyMode");'), True, expect_to_fail=True
            )
        # pylint: disable=redefined-outer-name
        except CliExecutionException as exc:
            self.starter.arangosh.run_command(
                ("delete collection", 'db._drop("checkReadOnlyMode");'), True, expect_to_fail=False
            )
            raise Exception("The system is not in read-only mode.") from exc
        assert (
            "ArangoError 11: cannot create collection" in result[1]
        ), "Expected error message not found in arangosh output."

    @step
    def check_not_readonly(self):
        """check that system is not in read-only mode"""
        try:
            self.starter.arangosh.run_command(
                ("try to create collection", 'db._create("checkNotReadOnlyMode");'), True, expect_to_fail=False
            )
        # pylint: disable=redefined-outer-name
        except CliExecutionException as exc:
            raise Exception("Couldn't create collection. The system is expected not to be in read-only mode.") from exc
        self.starter.arangosh.run_command(
            ("delete collection", 'db._drop("checkNotReadOnlyMode");'), True, expect_to_fail=False
        )

    def get_agents(self):
        """get a list of agents"""
        agents = []
        for starter in self.runner.starter_instances:
            for agent in starter.get_agents():
                agents.append(agent)
        return agents

    def get_server_id(self):
        """read server id from data dir"""
