import json
import shutil
from pathlib import Path
from time import time

import requests
from allure_commons._allure import attach

from arangodb.async_client import CliExecutionException
from arangodb.installers import create_config_installer_set, InstallerBaseConfig, RunProperties
from arangodb.instance import InstanceType
from arangodb.starter.deployments.activefailover import ActiveFailover
from arangodb.starter.deployments.cluster import Cluster
from arangodb.starter.deployments.dc2dc import Dc2Dc
from arangodb.starter.deployments.leaderfollower import LeaderFollower
from reporting.reporting_utils import step
from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite
from tools.external_helpers.license_generator.license_generator import create_license


class LicenseManagerBaseTestSuite(BaseTestSuite):
    def __init__(
        self,
        new_version,
        installer_base_config,
        child_classes=[],
    ):
        self.new_version=new_version
        self.base_cfg = installer_base_config
        super().__init__(child_classes=child_classes)
        self.parent_test_suite_name = "Licence manager test suite"
        self.auto_generate_parent_test_suite_name = False
        if self.__doc__:
            self.suite_name = self.__doc__
        else:
            self.suite_name = "Licence manager test suite"
        self.use_subsuite = False
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

    @step
    def tear_down_test_suite(self):
        """clean up the system after running tests"""
        self.runner.starter_shutdown()

    @step
    def setup_testcase(self):
        """prepare to run test case"""
        self.set_valid_license()

    @step
    def teardown_testcase(self):
        """clean up after test case"""
        pass

    def add_crash_data_to_report(self):
        self.save_log_file()
        self.save_data_dir()

    def save_log_file(self):
        if self.installer.instance and self.installer.instance.logfile.exists():
            log = open(self.installer.instance.logfile, "r").read()
            attach(log, "Log file " + str(self.installer.instance.logfile))

    def save_data_dir(self):
        data_dir = self.installer.cfg.dbdir
        if data_dir.exists():
            archive = shutil.make_archive("datadir", "bztar", data_dir, data_dir)
            attach.file(archive, "data directory archive", "application/x-bzip2", "tar.bz2")

    @step
    def check_that_license_is_not_expired(self, time_left_threshold=0):
        """check that license is not expired"""
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

    def send_request(self, method, url, data=None, headers={}, timeout=None, instance_type=None):
        if not instance_type:
            if isinstance(self.runner, LeaderFollower):
                instance_type = InstanceType.SINGLE
            elif isinstance(self.runner, ActiveFailover):
                instance_type = InstanceType.RESILIENT_SINGLE
            elif isinstance(self.runner, Cluster):
                instance_type = InstanceType.COORDINATOR
            elif isinstance(self.runner, Dc2Dc):
                instance_type = InstanceType.COORDINATOR
            else:
                instance_type = InstanceType.SINGLE
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
        resp = self.send_request(
            requests.get,
            "/_db/_system/_admin/license",
        )
        license = json.loads(resp[0].content)
        return license

    def set_license(self, license):
        raise NotImplementedError(f"Setting license not implemented for {type(self)}")

    @step
    def expire_license(self):
        """expire license"""
        new_timestamp = str(int(time() - 1))
        server_id = self.get_server_id()
        license = create_license(new_timestamp, server_id)
        self.set_license(license)

    @step
    def set_valid_license(self):
        """expire license"""
        new_timestamp = str(int(time() + 59 * 60))
        server_id = self.get_server_id()
        license = create_license(new_timestamp, server_id)
        self.set_license(license)

    @step
    def check_readonly(self):
        """check that system is in read-only mode"""
        try:
            result = self.starter.arangosh.run_command(
                ("try to create collection", 'db._create("checkReadOnlyMode");'), True, expect_to_fail=True
            )
        except CliExecutionException:
            self.starter.arangosh.run_command(
                ("delete collection", 'db._drop("checkReadOnlyMode");'), True, expect_to_fail=False
            )
            raise Exception("The system is not in read-only mode.")
        assert (
            "ArangoError 11: cannot create collection" in result[1]
        ), "Expected error message not found on arangosh output."

    @step
    def check_not_readonly(self):
        """check that system is not in read-only mode"""
        try:
            self.starter.arangosh.run_command(
                ("try to create collection", 'db._create("checkNotReadOnlyMode");'), True, expect_to_fail=False
            )
        except CliExecutionException:
            raise Exception("Couldn't create collection. The system is expected not to be in read-only mode.")
        self.starter.arangosh.run_command(
            ("delete collection", 'db._drop("checkNotReadOnlyMode");'), True, expect_to_fail=False
        )

    def get_agents(self):
        agents = []
        for starter in self.runner.starter_instances:
            for agent in starter.get_agents():
                agents.append(agent)
        return agents
