#!/usr/bin/env python3
""" baseclass to manage selenium UI tests """

from selenium import webdriver
from arangodb.starter.deployments import RunnerType
from arangodb.starter.deployments.selenium_deployments import SeleniumRunner

#pylint: disable=import-outside-toplevel
def init(runner_type: RunnerType,
         selenium_worker: str) -> SeleniumRunner:
    """ build selenium testcase for runner_type """
    driver_func = getattr(webdriver, selenium_worker)
    driver = driver_func()
    args = (runner_type, driver)

    if runner_type == RunnerType.LEADER_FOLLOWER:
        from arangodb.starter.deployments.selenium_deployments.leaderfollower import LeaderFollower
        return LeaderFollower(*args)

    if runner_type == RunnerType.ACTIVE_FAILOVER:
        from arangodb.starter.deployments.selenium_deployments.activefailover import ActiveFailover
        return ActiveFailover(*args)

    if runner_type == RunnerType.CLUSTER:
        from arangodb.starter.deployments.selenium_deployments.cluster import Cluster
        return Cluster(*args)

    if runner_type == RunnerType.DC2DC:
        from arangodb.starter.deployments.selenium_deployments.dc2dc import Dc2Dc
        return Dc2Dc(*args)

    if runner_type == RunnerType.DC2DCENDURANCE:
        from arangodb.starter.deployments.selenium_deployments.dc2dc_endurance import Dc2DcEndurance
        return Dc2DcEndurance(*args)

    if runner_type == RunnerType.NONE:
        from arangodb.starter.deployments.selenium_deployments.none import NoStarter
        return NoStarter(*args)

    raise Exception("unknown starter type")
