#!/usr/bin/env python3
""" test the UI of a leader follower setup """
import time
import platform

from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner
from selenium.common.exceptions import StaleElementReferenceException

from reporting.reporting_utils import step

WINVER = platform.win32_ver()


class Cluster(SeleniumRunner):
    """check the leader follower setup and its properties"""

    def __init__(self, webdriver, is_headless: bool, testrun_name: str, ssl: bool):
        # pylint: disable=W0235
        super().__init__(webdriver, is_headless, testrun_name, ssl)

    @step
    def check_old(self, cfg, leader_follower=False, expect_follower_count=2, retry_count=10):
        """check the integrity of the old system before the upgrade"""
        self.check_version(cfg)

        self.navbar_goto("nodes")
        table = self.cluster_get_nodes_table()
        row_count = 0
        for row in table:
            if row["state"] == "SERVING":
                row_count += 1

        self.progress("serving instances 6 / %d" % row_count)
        self.ui_assert(row_count == 6, "UI-Test: expected 6 instances")

        self.navbar_goto("cluster")
        node_count = self.cluster_dashboard_get_count()
        self.ui_assert(
            node_count["dbservers"] == "3",
            "UI-Test: expected 3 dbservers, got: " + node_count["dbservers"],
        )
        self.ui_assert(
            node_count["coordinators"] == "3",
            "UI-Test: expected 3 coordinators, got: " + node_count["coordinators"],
        )
        health_state = None
        count = 0
        while count < 10:
            health_state = self.get_health_state()
            if health_state == "NODES OK":
                break
            count += 1
            time.sleep(1)
        self.ui_assert(health_state == "NODES OK", "UI-Test: expected all nodes to be OK")

    @step
    def upgrade_deployment(self, old_cfg, new_cfg, timeout):
        old_ver = str(old_cfg.semver)
        new_ver = str(new_cfg.semver)
        self.navbar_goto("nodes")
        print(old_ver)
        print(new_ver)
        upgrade_done = False
        while not upgrade_done:
            try:
                table = self.cluster_get_nodes_table(300)
            except StaleElementReferenceException:
                self.progress(" skip once")

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
        self.web.refresh()
        ver = self.detect_version()
        self.progress(" ver %s is %s?" % (str(ver), new_ver))
        self.ui_assert(
            ver["version"].lower().startswith(new_ver),
            "UI-Test: wrong version after upgrade",
        )

    @step
    def jam_step_1(self, cfg):
        """check for one set of instances to go away"""
        self.web.refresh()
        time.sleep(2)
        self.navbar_goto("cluster")
        node_count = None
        done = False
        retry_count = 0
        while not done:
            # the wintendo is slow to notice that the hosts are gone.
            timeout = 500 if WINVER[0] else 50
            node_count = self.cluster_dashboard_get_count(timeout)

            done = (
                (node_count["dbservers"] == "2/3")
                and (node_count["coordinators"] == "2/3")
                and (self.get_health_state() != "NODES OK")
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

        self.ui_assert(
            node_count["dbservers"] == "2/3",
            "UI-Test: dbservers: " + node_count["dbservers"],
        )
        self.ui_assert(
            node_count["coordinators"] == "2/3",
            "UI-Test: coordinators: " + node_count["coordinators"],
        )
        health_state = self.get_health_state()
        self.ui_assert(
            health_state != "NODES OK",
            "UI-Test: expected health to be NODES OK, have: " + health_state,
        )

        self.navbar_goto("nodes")
        row_count = 0
        retry_count = 0
        while row_count != 4 and retry_count < 10:
            table = self.cluster_get_nodes_table(300)
            for row in table:
                if row["state"] == "SERVING":
                    row_count += 1
            retry_count += 1
            if row_count != 4:
                self.web.refresh()
                time.sleep(2)
                row_count = 0

        self.progress(" serving instances 6 / %d [%d]" % (row_count, retry_count))
        self.ui_assert(
            row_count == 4,
            "UI-Test: expect 2 instances to be offline have %d of 6" % row_count,
        )

        health_state = None
        count = 0
        while count < 10:
            health_state = self.get_health_state()
            if health_state != "NODES OK":
                break
            count += 1
            time.sleep(1)
        self.ui_assert(
            health_state != "NODES OK",
            "UI-Test: wrong health stame after jam: " + health_state,
        )

    @step
    def jam_step_2(self, cfg):
        self.navbar_goto("cluster")
        node_count = None
        done = False
        retry_count = 0
        while not done:
            node_count = self.cluster_dashboard_get_count()
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
        self.check_old(cfg)
