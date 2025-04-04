#!/usr/bin/env python3
""" base class for arangodb starter deployment selenium frontend tests """
from abc import ABC
import logging
import re
import time

from arangodb.starter.deployments.runner import RunnerProperties
from arangodb.starter.deployments.selenium_deployments.selenoid_swiper import cleanup_temp_files
from arangodb.starter.deployments.selenium_deployments.selenium_session_spawner import spawn_selenium_session
from allure_commons._allure import attach
from allure_commons.types import AttachmentType
from reporting.reporting_utils import step
from selenium.webdriver.common.by import By
from selenium.common.exceptions import InvalidSessionIdException

FNRX = re.compile("[\n@]*")




class SeleniumRunner(ABC):
    "abstract base class for selenium UI testing"
    # pylint: disable=line-too-long disable=too-many-public-methods disable=too-many-instance-attributes disable=too-many-arguments
    def __init__(self,
                 selenium_args,
                 properties: RunnerProperties,
                 testrun_name: str,
                 ssl: bool,
                 selenium_include_suites: list[str]):
        """hi"""
        self.ssl = ssl
        self.testrun_name = testrun_name
        self.state = ""
        self.success = True
        self.importer = None
        self.restorer = None
        self.ui_entrypoint_instance = None
        self.cfg = None
        self.new_cfg = None
        self.is_cluster = False
        self.test_results = []
        self.main_test_suite_list = []
        self.after_install_test_suite_list = []
        self.jam_step_2_test_suite_list = []
        self.wait_for_upgrade_test_suite_list = []
        self.selenium_include_suites = selenium_include_suites
        self.props = properties
        self.video_name = f"{properties.short_name}_{testrun_name}.mp4".replace( '\n', '_').replace('@', '_')
        mylist = list(
            selenium_args['selenium_driver_args'])
        mylist.append(f"selenoid:options=videoName={self.video_name}")
        selenium_args['selenium_driver_args'] = mylist
        (self.is_headless, self.webdriver, self.video_start_time) = spawn_selenium_session(**selenium_args)
        self.supports_console_flush = self.webdriver.capabilities["browserName"] == "chrome"
        self.original_window_handle = None
        time.sleep(3)
        self.webdriver.maximize_window()
        time.sleep(3)
        print(f"Video filename will be: {self.video_name}")

    def _cleanup_temp_files(self):
        cleanup_temp_files(self.is_headless)

    def set_instances(self, cfg, importer, restorer, ui_entrypoint_instance, new_cfg=None):
        """change the used frontend instance"""
        self.cfg = cfg
        self.importer = importer
        self.restorer = restorer
        self.ui_entrypoint_instance = ui_entrypoint_instance
        self.new_cfg = new_cfg

    def quit(self):
        """terminate the web driver"""
        print("Quitting Selenium")
        if self.webdriver is not None:
            print("stopping")
            try:
                self.webdriver.quit()
            except InvalidSessionIdException as ex:
                print(f"Selenium connection seems to be already gone:  {str(ex)}")
            self.webdriver = None
            self._cleanup_temp_files()
            print(f"Video filename {self.video_name} written")

    def progress(self, msg):
        """add something to the state..."""
        logging.info("UI-Test: " + msg)
        with step("UI test progress: " + msg):
            pass
        if len(self.state) > 0:
            self.state += "\n"
        self.state += "UI: " + msg

    def reset_progress(self):
        """done with one test. Flush status buffer."""
        self.state = ""

    def get_progress(self):
        """extract the current progress buffer"""
        ret = self.state + "\n"
        self.reset_progress()
        return ret

    @step
    def disconnect(self):
        """byebye"""
        self.progress("Close!")
        self.webdriver.close()

    @step
    def get_browser_log_entries(self):
        """get log entreies from selenium and add to python logger before returning"""
        print("B" * 80)
        loglevels = {"NOTSET": 0, "DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "SEVERE": 40, "CRITICAL": 50}
        slurped_logs = self.webdriver.get_log("browser")
        browserlog = logging.getLogger("browser")
        for entry in slurped_logs:
            print(entry["message"])
            # convert broswer log to python log format
            rec = browserlog.makeRecord(
                "%s.%s" % (browserlog.name, entry["source"]),
                loglevels.get("WARNING"),  # always log it as warn...
                # loglevels.get(entry['level']),
                ".",
                0,
                entry["message"],
                None,
                None,
            )
            rec.created = entry["timestamp"] / 1000  # log using original timestamp.. us -> ms
            # pylint: disable=broad-except
            try:
                # add browser log to python log
                browserlog.handle(rec)
                self.progress(entry["message"])
            except Exception as ex:
                print("caught exception during transfering browser logs: " + str(ex))
                print(entry)

    @step
    def take_screenshot(self, filename=None):
        """*snap*"""
        self.success = False
        if filename is None:
            filename = "%s_%s_exception_screenshot.png" % (
                FNRX.sub("", self.testrun_name),
                self.__class__.__name__,
            )

        self.progress("Taking screenshot")

        # pylint: disable=broad-except
        try:
            if self.webdriver is not None:
                if self.is_headless:
                    self.progress("taking full screenshot")
                    elmnt = self.webdriver.find_element(By.TAG_NAME, "body")
                    screenshot = elmnt.screenshot_as_png()
                else:
                    self.progress("taking screenshot")
                    screenshot = self.webdriver.get_screenshot_as_png()
            else:
                self.progress("webdriver is None. Cannot take a screenshot.")
                return
        except InvalidSessionIdException:
            self.progress("Fatal: webdriver not connected!")
            return
        except Exception as ex:
            self.progress("falling back to taking partial screenshot " + str(ex))
            screenshot = self.webdriver.get_screenshot_as_png()

        self.get_browser_log_entries()
        self.progress("Saving screenshot to file: %s" % filename)
        with open(filename, "wb") as file:
            file.write(screenshot)

        attach(
            screenshot,
            name="Screenshot ({fn})".format(fn=filename),
            attachment_type=AttachmentType.PNG,
        )

    # pylint: disable=no-else-return
    def get_protocol(self):
        """get HTTP protocol for this runner(http/https)"""
        if self.ssl:
            return "https"
        else:
            return "http"

    def test_after_jam_step_two(self):
        """check the integrity of the old system after jamming setup (first step)"""
        for test_suite_class in self.jam_step_2_test_suite_list:
            test_suite = test_suite_class(self)
            results = test_suite.run()
            self.test_results += results

    def test_empty_ui(self):
        """run all tests that expect the server to be empty"""

    def run_test_suites(self, suites):
        """run all test suites from a given list"""
        for suite_class in suites:
            test_suite = suite_class(self)
            results = test_suite.run()
            self.test_results += results

    def test_setup(self):
        """setup the testcases"""
        self.run_test_suites(self.main_test_suite_list)

    def test_after_install(self):
        """check the integrity of the old system before the upgrade"""
        self.run_test_suites(self.after_install_test_suite_list)

    def test_wait_for_upgrade(self):
        """perform tests after upgrade (check whether the versions in the table switch etc.)"""
        self.run_test_suites(self.wait_for_upgrade_test_suite_list)
