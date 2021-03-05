#!/usr/bin/env python3
""" test the UI of a leader follower setup """
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

class Cluster(SeleniumRunner):
    """ check the leader follower setup and its properties """
    def __init__(self, webdriver):
        super().__init__(webdriver)
