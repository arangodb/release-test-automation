#!/usr/bin/env python3
""" test the UI of a cluster setup """
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner
from selenium_ui_test.test_suites.basic_test_suite import BasicTestSuite
from selenium_ui_test.test_suites.cluster.wait_for_upgrade_test_suite import ClusterWaitForUpgradeTestSuite
from selenium_ui_test.test_suites.cluster.jam_1_test_suite import ClusterJamStepOneSuite
from selenium_ui_test.test_suites.cluster.jam_2_test_suite import ClusterJamStepTwoSuite


class Cluster(SeleniumRunner):
    """check the leader follower setup and its properties"""

    def __init__(self, selenium_args, testrun_name: str, ssl: bool, selenium_include_suites: list[str]):
        # pylint: disable=useless-super-delegation
        super().__init__(selenium_args, testrun_name, ssl, selenium_include_suites)
        self.is_cluster = True
        self.main_test_suite_list = [BasicTestSuite]
        self.wait_for_upgrade_test_suite_list = [ClusterWaitForUpgradeTestSuite]
        self.jam_step_1_test_suite_list = [ClusterJamStepOneSuite]
        self.jam_step_2_test_suite_list = [ClusterJamStepTwoSuite]

    def jam_step_1(self):
        """check the integrity of the old system after jamming setup (first step)"""
        self.run_test_suites(self.jam_step_1_test_suite_list)

    def jam_step_2(self):
        """check the integrity of the old system after jamming setup (second step)"""
        self.run_test_suites(self.jam_step_2_test_suite_list)
