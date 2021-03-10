#!/usr/bin/env python3
""" test the UI of a leader follower setup """
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

class LeaderFollower(SeleniumRunner):
    """ check the leader follower setup and its properties """
    def __init__(self, webdriver):
        super().__init__(webdriver)

    def check_old(self, cfg):
        """ check the integrity of the old system before the upgrade """
        ver = self.detect_version()
        assert ver['version'].lower().startswith(str(cfg.semver))
        if cfg.enterprise:
            assert ver['enterprise'] == 'ENTERPRISE EDITION'
        else:
            assert ver['enterprise'] == 'COMMUNITY EDITION'

        self.navbar_goto('replication')
        replication_table = self.get_replication_screen(True)
        print(replication_table)
        # head and one follower should be there:
        assert len(replication_table['follower_table']) == 2

    def upgrade_deployment(self, old_cfg, new_cfg):
        old_ver = str(old_cfg.semver)
        new_ver = str(new_cfg.semver)
        self.navbar_goto('nodes')
        print(old_ver)
        print(new_ver)
        upgrade_done = False
        while not upgrade_done:
            try:
                table = self.cluster_get_nodes_table(300)
            except StaleElementReferenceException:
                print("S: skip once")

            old_count = 0
            new_count = 0
            for row in table:
                print(row['version'])
                if row['version'].lower().startswith(old_ver):
                    old_count += 1
                elif row['version'].lower().startswith(new_ver):
                    new_count += 1
                else:
                    print("S: can't count this row on new or old: %s" % (str(row)))
            upgrade_done = (old_count == 0) and (new_count == 6)
            print('S: serving instances old %d / new %d' % (old_count, new_count))
            if not upgrade_done:
                time.sleep(5)
        # the version doesn't update automatically, force refresh:
        self.web.refresh()
        ver = self.detect_version()
        print("S: ver %s is %s?" % (str(ver), new_ver))
        assert ver['version'].lower().startswith(new_ver)

    def jam_step_1(self, cfg):
        """ check for one set of instances to go away """
        self.navbar_goto('replication')
        replication_table = self.get_replication_screen(True)
        print(replication_table)
        # head and one follower should be there:
        assert len(replication_table['follower_table']) == 2

    def jam_step_2(self, cfg):
        pass
