#!/usr/bin/env python3
""" test the UI of a leader follower setup """
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

class Dc2Dc(SeleniumRunner):
    """ check the leader follower setup and its properties """
    def __init__(self, webdriver):
        super().__init__(webdriver)

    def check_old(self, cfg):
        """ check the integrity of the old system before the upgrade """
        pass

    def upgrade_deployment(self, old_cfg, new_cfg):
        """ check the upgrade whether the versions in the table switch etc. """
        pass

    def jam_step_1(self, cfg):
        """ check the integrity of the old system before the upgrade """
        pass

    def jam_step_2(self, cfg):
        """ check the integrity of the old system before the upgrade """
        pass
