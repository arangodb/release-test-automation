#!/usr/bin/env python3
""" base class for arangodb starter deployment selenium frontend tests """
from abc import abstractmethod, ABC
import logging
import re
import time

from allure_commons._allure import attach
from allure_commons.types import AttachmentType
from reporting.reporting_utils import step, attach_table
from selenium.common.exceptions import InvalidSessionIdException

FNRX = re.compile("[\n@]*")


class SeleniumRunner(ABC):
    "abstract base class for selenium UI testing"
    # pylint: disable=C0301 disable=R0904
    def __init__(self, webdriver, is_headless: bool, testrun_name: str, ssl: bool):
        """hi"""
        self.ssl = ssl
        self.is_headless = is_headless
        self.testrun_name = testrun_name
        self.webdriver = webdriver
        self.original_window_handle = None
        self.state = ""
        time.sleep(3)
        self.webdriver.set_window_size(1600, 900)
        time.sleep(3)
        self.importer = None
        self.restorer = None
        self.ui_entrypoint_instance = None
        self.cfg = None
        self.new_cfg = None
        self.is_cluster = False
        self.test_results = []
        self.main_test_suite_list = []
        self.after_install_test_suite_list = []

    def set_instances(self, cfg, importer, restorer, ui_entrypoint_instance, new_cfg=None):
        """change the used frontend instance"""
        self.cfg = cfg
        self.importer = importer
        self.restorer = restorer
        self.ui_entrypoint_instance = ui_entrypoint_instance
        self.new_cfg = new_cfg

    def quit(self):
        """terminate the web driver"""
        if self.webdriver != None:
            self.webdriver.quit()
            self.webdriver = None

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
            # pylint: disable=W0703
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
        if filename is None:
            filename = "%s_%s_exception_screenshot.png" % (
                FNRX.sub("", self.testrun_name),
                self.__class__.__name__,
            )

        self.progress("Taking screenshot from: %s " % self.webdriver.current_url)
        # pylint: disable=W0703
        try:
            if self.is_headless:
                self.progress("taking full screenshot")
                elmnt = self.webdriver.find_element_by_tag_name("body")
                screenshot = elmnt.screenshot_as_png()
            else:
                self.progress("taking screenshot")
                screenshot = self.webdriver.get_screenshot_as_png()
        except InvalidSessionIdException:
            self.progress("Fatal: webdriver not connected!")
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

    # pylint: disable=R1705
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
        pass

    def run_test_suites(self, suites):
        """run all test suites from a given list"""
        for suite_class in suites:
            test_suite = suite_class(self)
            results = test_suite.run()
            self.test_results += results

    def test_setup(self):
        self.run_test_suites(self.main_test_suite_list)

    def test_after_install(self):
        """check the integrity of the old system before the upgrade"""
        self.run_test_suites(self.after_install_test_suite_list)

    def test_wait_for_upgrade(self):
        """perform tests after upgrade (check whether the versions in the table switch etc.)"""
        self.run_test_suites(self.wait_for_upgrade_test_suite_list)