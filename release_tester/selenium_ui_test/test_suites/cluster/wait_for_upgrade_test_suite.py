#!/usr/bin/env python3
""" cluster upgrade monitoring testsuite """
import time

from selenium.common.exceptions import StaleElementReferenceException
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.pages.nodes_page import NodesPage
from selenium_ui_test.test_suites.base_test_suite import testcase

from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite


class ClusterWaitForUpgradeTestSuite(BaseSeleniumTestSuite):
    """test cases to check the integrity of the old system after the upgrade (Cluster)"""

    @testcase
    def upgrade_deployment(self, timeout=30):
        """test cases to check the integrity of the old system after the upgrade (Cluster)"""
        old_cfg = self.cfg
        new_cfg = self.selenium_runner.new_cfg
        old_ver = str(old_cfg.semver)
        new_ver = str(new_cfg.semver)
        NavigationBarPage(self.webdriver).navbar_goto("nodes")
        print(old_ver)
        print(new_ver)
        upgrade_done = False
        while not upgrade_done:
            table = []
            try:
                table = NodesPage(self.webdriver).cluster_get_nodes_table(300)
            except StaleElementReferenceException:
                self.progress(" skip once")
                continue

            old_count = 0
            new_count = 0
            for row in table:
                print(row["version"])
                if row["version"].lower().startswith(old_ver):
                    old_count += 1
                elif row["version"].lower().startswith(new_ver):
                    new_count += 1
                else:
                    self.progress(" can't count this row on new or old: %s" % (str(row)))
            upgrade_done = (old_count == 0) and (new_count == 6)
            self.progress(" serving instances old %d / new %d" % (old_count, new_count))
            if not upgrade_done:
                time.sleep(5)
            timeout -= 1
            if timeout <= 0:
                raise TimeoutError("UI-Test: the cluster UI didn't show the new version in time")
        # the version doesn't update automatically, force refresh:
        self.webdriver.refresh()
        ver = NavigationBarPage(self.webdriver).detect_version()
        self.progress(" ver %s is %s?" % (str(ver), new_ver))
        self.ui_assert(ver["version"].lower().startswith(new_ver), "UI-Test: wrong version after upgrade")
        # TODO self.check_full_ui(new_cfg)
