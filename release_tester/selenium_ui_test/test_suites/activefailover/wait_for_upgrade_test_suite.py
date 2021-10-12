import pprint
import time
from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite, testcase
from selenium_ui_test.pages.navbar import NavigationBarPage

from selenium_ui_test.pages.replication_page import ReplicationPage


class ActiveFailoverWaitForUpgradeTestSuite(BaseTestSuite):
    """test cases to check the integrity of the old system after the upgrade (Active failover)"""

    @testcase
    def check_version_before_upgrade(self):
        self.check_version(self.selenium_runner.new_cfg.semver, self.is_enterprise)

    @testcase
    def check_follower_count(self, expect_follower_count=2, retry_count=10):
        """check the integrity of the old system after the install"""
        while retry_count > 0:
            NavigationBarPage(self.webdriver).navbar_goto("replication")
            replication_page = ReplicationPage(self.webdriver)
            replication_table = replication_page.get_replication_screen(True)
            print(replication_table)
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
