#!/usr/bin/env python3
""" baseclass to manage selenium UI tests """

import time

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException

from arangodb.starter.deployments import RunnerType
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner

# pylint: disable=import-outside-toplevel disable=too-many-locals disable=too-many-branches disable=too-many-statements
def init(
    runner_type: RunnerType,
    selenium_worker: str,
    selenium_driver_args: list,
    testrun_name: str,
    ssl: bool,
) -> SeleniumRunner:
    """build selenium testcase for runner_type"""
    if '_' in selenium_worker:
        sw_split = selenium_worker.split('_')
        driver_func = getattr(webdriver, sw_split[0])
        selenium_worker = sw_split[1].lower()
        worker_options = ""
    else:
        driver_func = getattr(webdriver, selenium_worker)
        worker_options = selenium_worker = selenium_worker.lower() + "_"
    if driver_func is None:
        raise Exception("webdriver " + selenium_worker + "unknown")

    kwargs = {}
    is_headless = False
    if len(selenium_driver_args) > 0:
        opts_func = getattr(webdriver, selenium_worker)
        opts_func = getattr(opts_func, "options")
        opts_func = getattr(opts_func, "Options")
        options = opts_func()
        kwargs[worker_options + "options"] = options
        for opt in selenium_driver_args:
            split_opts = opt.split('=')
            if opt == "headless":
                is_headless = True
            elif len(split_opts) == 2:
                if split_opts[0] == 'command_executor':
                    kwargs['command_executor'] = split_opts[1]
                    continue
            elif len(split_opts) >= 3:
                key=split_opts.pop(0)
                where_to_put = {}
                while len(split_opts) > 2:
                    if split_opts[0] not in where_to_put:
                        where_to_put[split_opts[0]] = {}
                    where_to_put = where_to_put[split_opts[0]]
                if len(split_opts) == 2:
                    val = split_opts[1]
                    if val == 'True':
                        val = True
                    elif val == 'False':
                        val = False
                    where_to_put[split_opts[0]] = val
                    options.set_capability(key, where_to_put)
                    split_opts=[]
                continue
            options.add_argument("--" + opt)

    driver = None
    count = 0
    while driver is None and count < 10:
        count += 1
        try:
            driver = driver_func(**kwargs)
        except TypeError:
            try:
                driver = driver_func.webdriver.WebDriver(**kwargs)
            except SessionNotCreatedException as ex:
                if count == 10:
                    raise ex
                print("S: retrying to launch browser")
                time.sleep(2)
        except SessionNotCreatedException as ex:
            if count == 10:
                raise ex
            print("S: retrying to launch browser")
            time.sleep(2)
    if selenium_worker.lower() == "chrome":
        required_width = driver.execute_script("return document.body.parentNode.scrollWidth")
        required_height = driver.execute_script("return document.body.parentNode.scrollHeight")
        driver.set_window_size(required_width, required_height)

    if runner_type == RunnerType.SINGLE:
        from arangodb.starter.deployments.selenium_deployments.single import (
            Single,
        )

        return Single(driver, is_headless, testrun_name, ssl)

    if runner_type == RunnerType.LEADER_FOLLOWER:
        from arangodb.starter.deployments.selenium_deployments.leaderfollower import (
            LeaderFollower,
        )

        return LeaderFollower(driver, is_headless, testrun_name, ssl)

    if runner_type == RunnerType.ACTIVE_FAILOVER:
        from arangodb.starter.deployments.selenium_deployments.activefailover import (
            ActiveFailover,
        )

        return ActiveFailover(driver, is_headless, testrun_name, ssl)

    if runner_type == RunnerType.CLUSTER:
        from arangodb.starter.deployments.selenium_deployments.cluster import Cluster

        return Cluster(driver, is_headless, testrun_name, ssl)

    if runner_type == RunnerType.DC2DC:
        from arangodb.starter.deployments.selenium_deployments.dc2dc import Dc2Dc

        return Dc2Dc(driver, is_headless, testrun_name, ssl)

    if runner_type == RunnerType.DC2DCENDURANCE:
        from arangodb.starter.deployments.selenium_deployments.dc2dc_endurance import (
            Dc2DcEndurance,
        )

        return Dc2DcEndurance(driver, is_headless, testrun_name, ssl)

    if runner_type == RunnerType.NONE:
        from arangodb.starter.deployments.selenium_deployments.none import NoStarter

        return NoStarter(driver, is_headless, testrun_name, ssl)

    raise Exception("unknown starter type")
