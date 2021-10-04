from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner
from selenium_ui_test.test_suites.basic_test_suite import BasicTestSuite
from selenium_ui_test.test_suites.cluster.before_upgrade_test_suite import \
    ClusterBeforeUpgradeTestSuite
from selenium_ui_test.test_suites.cluster.after_upgrade_test_suite import \
    ClusterAfterUpgradeTestSuite
from selenium_ui_test.test_suites.cluster.jam_1_test_suite import ClusterJamStepOneSuite
from selenium_ui_test.test_suites.cluster.jam_2_test_suite import ClusterJamStepTwoSuite


class Cluster(SeleniumRunner):
    """ check the leader follower setup and its properties """
    def __init__(self, webdriver,
                 is_headless: bool,
                 testrun_name: str,
                 ssl: bool):
        # pylint: disable=W0235
        super().__init__(webdriver,
                         is_headless,
                         testrun_name,
                         ssl)
        self.is_cluster = True
        self.main_test_suite_list = [BasicTestSuite]
        self.before_upgrade_test_suite_list = [ClusterBeforeUpgradeTestSuite]
        self.after_upgrade_test_suite_list = [ClusterAfterUpgradeTestSuite]
        self.jam_step_1_test_suite_list = [ClusterJamStepOneSuite]
        self.jam_step_2_test_suite_list = [ClusterJamStepTwoSuite]