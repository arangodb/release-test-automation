#!/usr/bin/env python3
""" test the UI of a leader follower setup """
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

class Dc2DcEndurance(SeleniumRunner):
    """ check the leader follower setup and its properties """
    def __init__(self, webdriver,
                 is_headless: bool,
                 testrun_name: str):
        super().__init__(webdriver,
                         is_headless,
                         testrun_name)
