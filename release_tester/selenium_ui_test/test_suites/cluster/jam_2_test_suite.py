#!/usr/bin/python3
"""cluster jamming steps"""
import time
from selenium_ui_test.pages.nodes_page import NodesPage
from selenium_ui_test.pages.cluster_page import ClusterPage
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from test_suites_core.base_test_suite import testcase


class ClusterJamStepTwoSuite(BaseSeleniumTestSuite):
    """cluster jamming steps"""

    @testcase
    def jam_step_2(self):
        """ step 2 jamming: check the instances are gone from the table """
        NavigationBarPage(self.webdriver, self.cfg).navbar_goto("cluster")
        cluster_page = ClusterPage(self.webdriver, self.cfg)
        node_count = None
        done = False
        retry_count = 0
        while not done:
            node_count = cluster_page.cluster_dashboard_get_count()
            done = (node_count["dbservers"] == "3") and (node_count["coordinators"] == "3")
            if not done:
                time.sleep(3)
            retry_count += 1
            self.ui_assert(
                retry_count < 10,
                "UI-Test: expected 3 instances each, have: DB "
                + node_count["dbservers"]
                + " C "
                + node_count["coordinators"],
            )
        # self.check_old(cfg)
        # TODO self.check_full_ui(cfg)

    @testcase
    def after_jam_step_2(self):
        """check the integrity of the system after recovery from cluster failure"""
        version = (
            self.selenium_runner.new_cfg.version if self.selenium_runner.new_cfg else self.selenium_runner.cfg.version
        )
        self.check_version(version, self.is_enterprise)

        NavigationBarPage(self.webdriver, self.cfg).navbar_goto("nodes")
        nodes_page = NodesPage(self.webdriver, self.cfg)
        table = nodes_page.cluster_get_nodes_table()
        row_count = 0
        for row in table:
            if row["state"] == "SERVING":
                row_count += 1

        self.progress("serving instances 6 / %d" % row_count)
        self.ui_assert(row_count == 6, "UI-Test: expected 6 instances")

        nodes_page.navbar_goto("cluster")
        cluster_page = ClusterPage(self.webdriver, self.cfg)
        node_count = cluster_page.cluster_dashboard_get_count()
        self.ui_assert(node_count["dbservers"] == "3", "UI-Test: expected 3 dbservers, got: " + node_count["dbservers"])
        self.ui_assert(
            node_count["coordinators"] == "3", "UI-Test: expected 3 coordinators, got: " + node_count["coordinators"]
        )
        health_state = None
        count = 0
        while count < 10:
            health_state = cluster_page.get_health_state()
            if health_state == "NODES OK":
                break
            count += 1
            time.sleep(1)
        self.ui_assert(health_state == "NODES OK", "UI-Test: expected all nodes to be OK")
