#!/usr/bin/env python3
""" test the UI of a leader follower setup """
import time
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

class Cluster(SeleniumRunner):
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
        
        self.navbar_goto('nodes')
        time.sleep(3)
        table = self.cluster_get_nodes_table()
        rowCount = 0
        for row in table:
            if row['state'] == 'SERVING':
                rowCount += 1

        print('S: serving instances 6 / %d' % rowCount)
        assert rowCount == 6
        time.sleep(3)

        self.navbar_goto('cluster')
        time.sleep(3)
        node_count = self.cluster_dashboard_get_count()
        assert node_count['dbservers'] == '3'
        assert node_count['coordinators'] == '3'
        health_state = self.get_health_state()
        assert health_state == 'NODES OK'

    def upgrade_deployment(self, old_cfg, new_cfg):
        old_ver = str(old_cfg.semver)
        new_ver = str(new_cfg.semver)
        table = self.cluster_get_nodes_table()
        upgrade_done = False
        while not upgrade_done:
            old_count = 0;
            new_count = 1
            for row in table:
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

    def jam_step_1(self, cfg):
        """ check for one set of instances to go away """
        self.navbar_goto('cluster')
        time.sleep(3)
        node_count = None
        done = False
        retry_count = 0
        while not done:
            node_count = self.cluster_dashboard_get_count()

            done = ((node_count['dbservers'] == '2/3') and
                    (node_count['coordinators'] == '2/3') and
                    (self.get_health_state() != 'NODES OK'))
            if not done:
                time.sleep(3)
            retry_count += 1
            assert retry_count < 20
            
        assert node_count['dbservers'] == '2/3'
        assert node_count['coordinators'] == '2/3'
        health_state = self.get_health_state()
        assert health_state != 'NODES OK'

        self.navbar_goto('nodes')
        time.sleep(10)
        table = self.cluster_get_nodes_table()
        rowCount = 0
        for row in table:
            if row['state'] == 'SERVING':
                rowCount += 1

        print('S: serving instances 6 / %d' % rowCount)
        assert rowCount == 4
        time.sleep(3)

        health_state = self.get_health_state()
        assert health_state != 'NODES OK'

    def jam_step_2(self, cfg):
        self.navbar_goto('cluster')
        time.sleep(3)
        node_count = None
        done = False
        retry_count = 0
        while not done:
            node_count = self.cluster_dashboard_get_count()
            done = (node_count['dbservers'] == '3') and (node_count['coordinators'] == '3')
            if not done:
                time.sleep(3)
            retry_count += 1
            assert retry_count < 10
        self.check_old(cfg)
