#!/usr/bin/env python
"""active failover base testsuite"""
import pprint
import time
from selenium_ui_test.test_suites.base_selenium_test_suite import BaseSeleniumTestSuite
from selenium_ui_test.pages.navbar import NavigationBarPage

from selenium_ui_test.pages.replication_page import ReplicationPage


class ActiveFailoverBaseTestSuite(BaseSeleniumTestSuite):
    """testsuite to be run to check the follower count"""

    def check_follower_count(self, expect_follower_count=2, retry_count=10):
        """check the integrity of the old system after the install"""
        while retry_count > 0:
            NavigationBarPage(self.webdriver, self.cfg, self.video_start_time).navbar_goto("replication")
            replication_page = ReplicationPage(self.webdriver, self.cfg, self.video_start_time)
            replication_table = replication_page.get_replication_screen(True)
            self.tprint(replication_table)
            if len(replication_table["follower_table"]) != expect_follower_count + 1:
                time.sleep(5)
                retry_count -= 1
            else:
                retry_count = 0  # its there!
        # head and two followers should be there:
        self.progress(
            " expecting %d followers, have %d followers"
            % (expect_follower_count, len(replication_table["follower_table"]) - 1)
        )
        self.ui_assert(
            len(replication_table["follower_table"]) == expect_follower_count + 1,
            "UI-Test:\nexpect 1 follower in:\n%s" % pprint.pformat(replication_table),
        )
    
    def check_replication_tab(self):
        """checking replication tab information"""
        replication_page = ReplicationPage(self.webdriver, self.cfg, self.video_start_time)
        replication_page.get_replication_information()
