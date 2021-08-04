#!/usr/bin/env python3
""" test the UI of a active failover setup """
import time
import pprint
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

from reporting.reporting_utils import step


class ActiveFailover(SeleniumRunner):
    """ check the active failover setup and its properties """
    def __init__(self, webdriver,
                 is_headless: bool,
                 testrun_name: str):
        # pylint: disable=W0235
        super().__init__(webdriver,
                         is_headless,
                         testrun_name)

    @step
    def check_old(self, cfg, leader_follower=False, expect_follower_count=2, retry_count=10):
        """ check the integrity of the old system before the upgrade """
        self.check_version(cfg)

        while retry_count > 0:
            self.navbar_goto('replication')
            replication_table = self.get_replication_screen(True)
            print(replication_table)
            if len(replication_table['follower_table']) != expect_follower_count + 1:
                time.sleep(5)
                retry_count -= 1
            else:
                retry_count = 0 # its there!
        # head and two followers should be there:
        self.progress(' expecting %d followers, have %d followers'%(
            expect_follower_count, len(replication_table['follower_table']) - 1))
        self.ui_assert(len(replication_table['follower_table']) == expect_follower_count + 1,
                       "UI-Test:\nexpect 1 follower in:\n%s" % pprint.pformat(
                           replication_table))

    @step
    def upgrade_deployment(self, old_cfg, new_cfg, timeout):
        """ nothing to see here """

    @step
    def jam_step_1(self, cfg):
        """ check for one set of instances to go away """
        self.navbar_goto('replication')
        replication_table = self.get_replication_screen(True)
        print(replication_table)
        # head and one follower should be there:
        self.ui_assert(len(replication_table['follower_table']) == 2,
                       "UI-Test:\nexpect 2 followers in:\n %s" % pprint.pformat(
                           replication_table))
        self.check_full_ui(cfg)

    def jam_step_2(self, cfg):
        pass
