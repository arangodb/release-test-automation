#!/usr/bin/env python3
""" cluster jam step 1 testsuite """
import platform
import time
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite

from selenium_ui_test.pages.cluster_page import ClusterPage
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.pages.nodes_page import NodesPage
from selenium_ui_test.test_suites.base_test_suite import testcase


class ClusterJamStepOneSuite(BaseSeleniumTestSuite):
    """ cluster jam step 1 testsuite """
    WINVER = platform.win32_ver()

    @testcase
    def jam_step_1(self):
        """check for one set of instances to go away"""
        self.webdriver.refresh()
        time.sleep(2)
        NavigationBarPage(self.webdriver, self.cfg).navbar_goto("cluster")
        cluster_page = ClusterPage(self.webdriver, self.cfg)
        node_count = None
        done = False
        retry_count = 0
        while not done:
            # the wintendo is slow to notice that the hosts are gone.
            timeout = 500 if self.WINVER[0] else 50
            node_count = cluster_page.cluster_dashboard_get_count(timeout)

            done = (
                (node_count["dbservers"] == "2/3")
                and (node_count["coordinators"] == "2/3")
                and (cluster_page.get_health_state() != "NODES OK")
            )
            self.ui_assert(
                retry_count < 40,
                "UI-Test: Timeout: expected db + c to be 2/3, have: "
                + node_count["dbservers"]
                + ", "
                + node_count["coordinators"],
            )
            if not done:
                time.sleep(3)
            retry_count += 1

        self.ui_assert(node_count["dbservers"] == "2/3", "UI-Test: dbservers: " + node_count["dbservers"])
        self.ui_assert(node_count["coordinators"] == "2/3", "UI-Test: coordinators: " + node_count["coordinators"])
        health_state = cluster_page.get_health_state()
        self.ui_assert(health_state != "NODES OK", "UI-Test: expected health to be NODES OK, have: " + health_state)

        NavigationBarPage(self.webdriver, self.cfg).navbar_goto("nodes")
        nodes_page = NodesPage(self.webdriver, self.cfg)
        row_count = 0
        retry_count = 0
        while row_count != 4 and retry_count < 10:
            table = nodes_page.cluster_get_nodes_table(300)
            for row in table:
                if row["state"] == "SERVING":
                    row_count += 1
            retry_count += 1
            if row_count != 4:
                self.webdriver.refresh()
                time.sleep(2)
                row_count = 0

        self.progress(" serving instances 6 / %d [%d]" % (row_count, retry_count))
        self.ui_assert(row_count == 4, "UI-Test: expect 2 instances to be offline have %d of 6" % row_count)

        health_state = None
        count = 0
        while count < 10:
            health_state = nodes_page.get_health_state()
            if health_state != "NODES OK":
                break
            count += 1
            time.sleep(1)
        self.ui_assert(health_state != "NODES OK", "UI-Test: wrong health stame after jam: " + health_state)
        # TODO self.check_full_ui(cfg)
