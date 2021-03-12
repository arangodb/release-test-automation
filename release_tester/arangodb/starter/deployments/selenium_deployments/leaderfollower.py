#!/usr/bin/env python3
""" test the UI of a leader follower setup """
import time
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

class LeaderFollower(SeleniumRunner):
    """ check the leader follower setup and its properties """
    def __init__(self, webdriver):
        super().__init__(webdriver)
        
    def check_old(self, cfg, leader_follower=True):
        """ check the integrity of the old system before the upgrade """
        ver = self.detect_version()
        print('S: %s ~= %s?'% (ver['version'].lower(), str(cfg.semver)))
        
        assert ver['version'].lower().startswith(str(cfg.semver))
        if cfg.enterprise:
            assert ver['enterprise'] == 'ENTERPRISE EDITION'
        else:
            assert ver['enterprise'] == 'COMMUNITY EDITION'

        count = 0
        replication_table = None
        while True:
            self.navbar_goto('replication')
            replication_table = self.get_replication_screen(leader_follower, 120)
            print(replication_table)
            if len(replication_table['follower_table']) == 2:
                break
            else:
                time.sleep(5)
        # head and one follower should be there:
        assert len(replication_table['follower_table']) == 2
        
    def upgrade_deployment(self, new_cfg, secondary, leader_follower):
        pass

    def jam_step_1(self, cfg):
        """ check for one set of instances to go away """
        self.navbar_goto('replication')
        replication_table = self.get_replication_screen(True)
        print(replication_table)
        # head and one follower should be there:
        assert len(replication_table['follower_table']) == 2

    def jam_step_2(self, cfg):
        pass
