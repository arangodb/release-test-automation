#!/usr/bin/env python3
""" baseclass to manage selenium UI tests """

import time

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException

from arangodb.starter.deployments import RunnerType
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

#pylint: disable=import-outside-toplevel
def init(runner_type: RunnerType,
         selenium_worker: str,
         selenium_driver_args: list,
         testrun_name: str) -> SeleniumRunner:
    """ build selenium testcase for runner_type """
    driver_func = getattr(webdriver, selenium_worker)
    if driver_func is None:
        raise Exception("webdriver " + selenium_worker + "unknown")
    # from selenium.webdriver.chrome.options import Options
    kwargs = {}
    is_headless = False
    if len(selenium_driver_args) > 0:
        selenium_worker = selenium_worker.lower()
        opts_func = getattr(webdriver, selenium_worker)
        opts_func = getattr(opts_func, 'options')
        opts_func = getattr(opts_func, 'Options')
        options = opts_func()
        kwargs[selenium_worker +'_options'] = options
        for opt in selenium_driver_args:
            if opt == 'headless':
                is_headless = True
            options.add_argument('--' + opt)
    # kwargs['service_log_path'] = "/tmp/abcd123.log"
    driver = None
    count = 0
    while driver is None and count < 10:
        count += 1
        try:
            driver = driver_func(**kwargs)
        except SessionNotCreatedException as ex:
            if count == 10:
                raise ex
            print('S: retrying to launch browser')
            time.sleep(2)
    if selenium_worker.lower() == 'chrome':
        required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
        required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
        driver.set_window_size(required_width, required_height)

    if runner_type == RunnerType.LEADER_FOLLOWER:
        from arangodb.starter.deployments.selenium_deployments.leaderfollower import LeaderFollower
        return LeaderFollower(driver,
                              is_headless,
                              testrun_name)

    if runner_type == RunnerType.ACTIVE_FAILOVER:
        from arangodb.starter.deployments.selenium_deployments.activefailover import ActiveFailover
        return ActiveFailover(driver,
                              is_headless,
                              testrun_name)

    if runner_type == RunnerType.CLUSTER:
        from arangodb.starter.deployments.selenium_deployments.cluster import Cluster
        return Cluster(driver,
                       is_headless,
                       testrun_name)

    if runner_type == RunnerType.DC2DC:
        from arangodb.starter.deployments.selenium_deployments.dc2dc import Dc2Dc
        return Dc2Dc(driver,
                     is_headless,
                     testrun_name)

    if runner_type == RunnerType.DC2DCENDURANCE:
        from arangodb.starter.deployments.selenium_deployments.dc2dc_endurance import Dc2DcEndurance
        return Dc2DcEndurance(driver,
                              is_headless,
                              testrun_name)

    if runner_type == RunnerType.NONE:
        from arangodb.starter.deployments.selenium_deployments.none import NoStarter
        return NoStarter(driver,
                         is_headless,
                         testrun_name)

    raise Exception("unknown starter type")
