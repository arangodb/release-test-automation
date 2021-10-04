import time

from selenium.common.exceptions import StaleElementReferenceException
from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.pages.nodes_page import NodesPage
from selenium_ui_test.test_suites.base_classes.before_upgrade_test_suite import \
    BeforeUpgradeTestSuite
from selenium_ui_test.pages.cluster_page import ClusterPage


class ClusterBeforeUpgradeTestSuite(BeforeUpgradeTestSuite):
    """ test cases to check the integrity of the old system before the upgrade (Cluster) """

    @testcase
    def check_old(self):
        """ check the integrity of the old system before the upgrade """
        self.check_version()

        NavigationBarPage(self.webdriver).navbar_goto('nodes')
        nodes_page = NodesPage(self.webdriver)
        table = nodes_page.cluster_get_nodes_table()
        row_count = 0
        for row in table:
            if row['state'] == 'SERVING':
                row_count += 1

        self.progress('serving instances 6 / %d' % row_count)
        self.ui_assert(row_count == 6, "UI-Test: expected 6 instances")

        nodes_page.navbar_goto('cluster')
        cluster_page = ClusterPage(self.webdriver)
        node_count = cluster_page.cluster_dashboard_get_count()
        self.ui_assert(node_count['dbservers'] == '3',
                       "UI-Test: expected 3 dbservers, got: " + node_count['dbservers'])
        self.ui_assert(node_count['coordinators'] == '3',
                       "UI-Test: expected 3 coordinators, got: " + node_count['coordinators'])
        health_state = None
        count = 0
        while count < 10:
            health_state = cluster_page.get_health_state()
            if health_state == 'NODES OK':
                break
            count += 1
            time.sleep(1)
        self.ui_assert(health_state == 'NODES OK', "UI-Test: expected all nodes to be OK")
