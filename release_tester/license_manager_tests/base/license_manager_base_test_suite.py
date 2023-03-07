"""base class for license manager test suites"""
import json
from time import time

import requests

# pylint: disable=import-error
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

    # pylint: disable=too-many-instance-attributes disable=dangerous-default-value
    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        if (
            self.new_version is not None
            and self.new_version < "3.9.0-nightly"
            or self.old_version is not None
            and self.old_version < "3.9.0-nightly"
        ):
            self.__class__.is_disabled = True
            self.__class__.disable_reasons.append(
                "License manager test suite is only applicable to versions 3.9 and newer."
            )
        self.sub_suite_name = self.__doc__ if self.__doc__ else self.__class__.__name__
        self.installer_set = create_config_installer_set(
            versions=[self.old_version, self.new_version] if self.old_version else [self.new_version],
            base_config=self.base_cfg,
            deployment_mode="all",
            run_properties=self.run_props,
            use_auto_certs=False,
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
        # pylint: disable=redefined-builtin
        license = self.get_license()
        license_expiry_timestamp = license["features"]["expires"]
        time_left = license_expiry_timestamp - time()
        if time_left >= 0:
            message = f"License expires in {time_left} seconds."
        else:
            message = f"License expired {-1*time_left} seconds ago."
        assert (
            time_left > time_left_threshold
        ), f"{message} Expected time left: more than {time_left_threshold} seconds."

    def get_default_instance_type(self):
        """get the instance type we should communicate with"""
        raise NotImplementedError(f"Default instance type is not set for {type(self)}")

    # pylint: disable=too-many-arguments
    def send_request(self, method, url, data=None, headers={}, timeout=None, instance_type=None):
        """send HTTP request to an instance"""
        if not instance_type:
            instance_type = self.get_default_instance_type()
        resp = self.starter.send_request(
            instance_type=instance_type,
            verb_method=method,
            url=url,
            data=data,
            headers=headers,
            timeout=timeout,
        )
        return resp

    def get_license(self):
        """read current license via REST API"""
        resp = self.send_request(
            requests.get,
            "/_db/_system/_admin/license",
        )
        # pylint: disable=redefined-builtin
        license = json.loads(resp[0].content)
        return license

    # pylint: disable=redefined-builtin
    def set_license(self, license):
        """set new license"""
        raise NotImplementedError(f"Setting license not implemented for {type(self)}")

    @step
    def expire_license(self):
        """expire license"""
        # pylint: disable=assignment-from-no-return
        new_timestamp = str(int(time() - 1))
        server_id = self.get_server_id()
        # pylint: disable=redefined-builtin
        license = create_license(new_timestamp, server_id)
        self.set_license(license)

    # pylint: disable=fixme
    # FIXME: set valid license before each test case
    #    @run_before_each_testcase
    def set_valid_license(self):
        """set valid license"""
        new_timestamp = str(int(time() + 59 * 60))
        # pylint: disable=assignment-from-no-return
        server_id = self.get_server_id()
        # pylint: disable=redefined-builtin
        license = create_license(new_timestamp, server_id)
        self.set_license(license)

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
