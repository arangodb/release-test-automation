from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.cluster_page import ClusterPage
from selenium_ui_test.pages.navbar import NavigationBarPage
import time


class ClusterJamStepTwoSuite(BaseTestSuite):
    @testcase
    def jam_step_2(self):
        NavigationBarPage(self.webdriver).navbar_goto('cluster')
        cluster_page = ClusterPage(self.webdriver)
        node_count = None
        done = False
        retry_count = 0
        while not done:
            node_count = cluster_page.cluster_dashboard_get_count()
            done = (node_count['dbservers'] == '3') and (node_count['coordinators'] == '3')
            if not done:
                time.sleep(3)
            retry_count += 1
            self.ui_assert(retry_count < 10,
                           "UI-Test: expected 3 instances each, have: DB " +
                           node_count['dbservers'] + " C " + node_count['coordinators'])
        # self.check_old(cfg)
        # TODO self.check_full_ui(cfg)
