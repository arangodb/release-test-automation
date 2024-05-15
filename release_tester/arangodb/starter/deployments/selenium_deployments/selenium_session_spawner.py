#!/usr/bin/env python3
""" baseclass to manage selenium UI tests """

import time

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException

from arangodb.starter.deployments.selenium_deployments.selenoid_swiper import cleanup_temp_files

# pylint: disable=import-outside-toplevel disable=too-many-locals
# pylint: disable=too-many-branches disable=too-many-statements
# pylint: disable=too-many-return-statements
def spawn_selenium_session(selenium_worker: str,  selenium_driver_args: list):
    """ launch selenium if prompted and return the instance """
    print(f"selenium worker {selenium_worker}")
    if "_" in selenium_worker:
        sw_split = selenium_worker.split("_")
        driver_func = getattr(webdriver, sw_split[0])
        selenium_worker = sw_split[1].lower()
        worker_options = ""
    else:
        driver_func = getattr(webdriver, selenium_worker)
        selenium_worker = selenium_worker.lower()
        worker_options = ""
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
        selenoid_options = {}
        for opt in selenium_driver_args:
            split_opts = opt.split("=")
            if opt == "headless":
                is_headless = True
            elif len(split_opts) == 2:
                if split_opts[0] == "command_executor":
                    is_headless = True
                    kwargs["command_executor"] = split_opts[1]
                    continue
            elif len(split_opts) >= 3:
                key = split_opts.pop(0)
                where_to_put = {}
                while len(split_opts) > 2:
                    if split_opts[0] not in where_to_put:
                        where_to_put[split_opts[0]] = {}
                    where_to_put = where_to_put[split_opts[0]]
                if len(split_opts) == 2:
                    val = split_opts[1]
                    if val == "True":
                        val = True
                    elif val == "False":
                        val = False
                    where_to_put[split_opts[0]] = val
                    if key == "selenoid:options":
                        selenoid_options.update(where_to_put)
                    else:
                        options.set_capability(key, where_to_put)
                    split_opts = []
                continue
            options.add_argument("--" + opt)
        options.set_capability("selenoid:options", selenoid_options)

    cleanup_temp_files(is_headless)
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
                cleanup_temp_files(is_headless)
                time.sleep(2)
        except SessionNotCreatedException as ex:
            if count == 10:
                raise ex
            print("S: retrying to launch browser")
            cleanup_temp_files(is_headless)
            time.sleep(2)
    if selenium_worker.lower() == "chrome":
        required_width = driver.execute_script("return document.body.parentNode.scrollWidth")
        required_height = driver.execute_script("return document.body.parentNode.scrollHeight")
        driver.set_window_size(required_width, required_height)
    return (is_headless, driver)
