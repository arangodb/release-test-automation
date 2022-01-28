"""base class for license manager test suites"""
import json
import shutil
from time import time

import requests
from allure_commons._allure import attach

# pylint: disable=import-error
from arangodb.async_client import CliExecutionException
from arangodb.installers import create_config_installer_set, RunProperties
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, run_after_suite, run_before_each_testcase
from tools.external_helpers.license_generator.license_generator import create_license


class LicenseManagerBaseTestSuite(BaseTestSuite):
    """base class for license manager test suites"""

    # pylint: disable=too-many-instance-attributes disable=dangerous-default-value
    def __init__(
        self,
        new_version,
        installer_base_config,
        child_classes=[],
    ):
        self.new_version = new_version
        self.base_cfg = installer_base_config
        package_type = ".tar.gz" if installer_base_config.zip_package else ".deb/.rpm/NSIS"
        self.suite_name = f"Licence manager test suite: ArangoDB v. {str(new_version)} ({package_type})"
        self.auto_generate_parent_test_suite_name = False
        super().__init__(child_classes=child_classes)
        self.use_subsuite = True
        run_props = RunProperties(
            enterprise=True,
            encryption_at_rest=False,
            ssl=False,
        )
        self.installer_set = create_config_installer_set(
            versions=[new_version], base_config=self.base_cfg, deployment_mode="all", run_properties=run_props
        )
        self.installer = self.installer_set[0][1]
        self.starter = None
        self.instance = None
        self.runner = None
        self.passvoid = "license_manager_tests"
        self.publicip = installer_base_config.publicip

    # pylint: disable=no-self-use
    def init_child_class(self, child_class):
        """initialise the child class"""
        return child_class(self.new_version, self.base_cfg)

    @run_after_suite
    def shutdown(self):
        """shutdown instance(s)"""
        self.runner.starter_shutdown()

    def add_crash_data_to_report(self):
        """save data dir and logs in case a test failed"""
        self.save_log_file()
        self.save_data_dir()

    def save_log_file(self):
        """add log file to the report"""
        if self.installer.instance and self.installer.instance.logfile.exists():
            log = open(self.installer.instance.logfile, "r").read()
            attach(log, "Log file " + str(self.installer.instance.logfile))

    def save_data_dir(self):
        """add datadir archive to the report"""
        data_dir = self.installer.cfg.dbdir
        if data_dir.exists():
            archive = shutil.make_archive("datadir", "bztar", data_dir, data_dir)
            attach.file(archive, "data directory archive", "application/x-bzip2", "tar.bz2")

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

    @run_before_each_testcase
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
