#!/usr/bin/env python3
""" test the UI of a leader follower setup """
from arangodb.starter.deployments.runner import RunnerProperties
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner


class NoStarter(SeleniumRunner):
    """check the leader follower setup and its properties"""

    def __init__(self, selenium_args,
                 properties: RunnerProperties,
                 testrun_name: str,
                 ssl: bool,
                 selenium_include_suites: list[str]):
        # pylint: disable=useless-super-delegation disable=too-many-arguments
        super().__init__(selenium_args, properties, testrun_name, ssl, selenium_include_suites)

    def check_old(self, cfg, leader_follower=False, expect_follower_count=2, retry_count=10):
        """check the integrity of the old system before the upgrade
        nothing to see here"""

    def upgrade_deployment(self, old_cfg, new_cfg, timeout):
        """check the upgrade whether the versions in the table switch etc.
        nothing to see here"""

    def jam_step_1(self, cfg):
        """check the integrity of the old system before the upgrade
        nothing to see here"""

    def jam_step_2(self, cfg):
        """check the integrity of the old system before the upgrade
        nothing to see here"""
