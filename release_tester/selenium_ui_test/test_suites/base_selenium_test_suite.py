#!/usr/bin/env python3
""" base class for all selenium testsuites """
import logging
from datetime import datetime

from beautifultable import BeautifulTable

from allure_commons._allure import attach
from allure_commons.types import AttachmentType
from selenium.common.exceptions import InvalidSessionIdException
from semver import VersionInfo

from selenium_ui_test.pages.base_page import BasePage
from selenium_ui_test.pages.login_page import LoginPage
from selenium_ui_test.pages.navbar import NavigationBarPage
from selenium_ui_test.test_suites.base_test_suite import BaseTestSuite
from reporting.reporting_utils import attach_table


class BaseSeleniumTestSuite(BaseTestSuite):
    """ base class for all selenium testsuites """
    # pylint: disable=dangerous-default-value disable=too-many-instance-attributes
    def __init__(self, selenium_runner, child_classes=[]):
        self.selenium_runner = selenium_runner
        super().__init__(child_classes)
        self.webdriver = selenium_runner.webdriver
        self.frontend = selenium_runner.ui_entrypoint_instance
        self.root_passvoid = self.frontend.get_passvoid()
        self.url = self.frontend.get_public_url()
        self.is_cluster = selenium_runner.is_cluster
        self.cfg = selenium_runner.cfg
        self.importer = selenium_runner.importer
        self.restore = selenium_runner.restorer
        self.test_data_dir = selenium_runner.cfg.test_data_dir.resolve()
        self.is_enterprise = selenium_runner.cfg.enterprise
        self.is_headless = selenium_runner.is_headless

    def init_child_class(self, child_class):
        return child_class(self.selenium_runner)

    def ui_assert(self, conditionstate, message):
        """python assert sucks. fuckit."""
        if not conditionstate:
            logging.error(message)
            self.take_screenshot()
            assert False, message

#    def connect_server_new_tab(self, cfg):
#        """login..."""
#        self.progress("Opening page")
#        print(frontend_instance[0].get_public_plain_url())
#        self.original_window_handle = self.webdriver.current_window_handle
#
#        # Open a new window
#        self.webdriver.execute_script("window.open('');")
#        self.webdriver.switch_to.window(self.webdriver.window_handles[1])
#        self.webdriver.get(
#            self.get_protocol()
#            + "://"
#            + self.frontend.get_public_plain_url()
#            + "/_db/_system/_admin/aardvark/index.html"
#        )
#        login_page = LoginPage(self.webdriver)
#        login_page.login_webif("root", frontend_instance[0].get_passvoid())
#
#    def close_tab_again(self):
#        """close a tab, and return to main window"""
#        self.webdriver.close()  # Switch back to the first tab with URL A
#        # self.webdriver.switch_to.window(self.webdriver.window_handles[0])
#        # print("Current Page Title is : %s" %self.webdriver.title)
#        # self.webdriver.close()
#        self.webdriver.switch_to.window(self.original_window_handle)
#        self.original_window_handle = None
#
#    def connect_server(self, frontend_instance, database, cfg):
#        """login..."""
#        self.progress("Opening page")
#        print(frontend_instance[0].get_public_plain_url())
#        self.webdriver.get(
#            self.get_protocol()
#            + "://"
#            + frontend_instance[0].get_public_plain_url()
#            + "/_db/_system/_admin/aardvark/index.html"
#        )
#        login_page = LoginPage(self.webdriver)
#        login_page.login_webif("root", frontend_instance[0].get_passvoid())

    def go_to_index_page(self):
        """Open index.html"""
        self.progress("Open index.html")
        path = "/_db/_system/_admin/aardvark/index.html"
        self.goto_url_and_wait_until_loaded(path)
        if "#login" in self.webdriver.current_url:
            login_page = LoginPage(self.webdriver)
            login_page.login_webif("root", self.root_passvoid, "_system")
            self.goto_url_and_wait_until_loaded(path)

    def go_to_dashboard(self, username="root", database_name="_system"):
        path = "/_db/_system/_admin/aardvark/index.html#dashboard"
        self.webdriver.get(self.url + path)
        if not path in self.webdriver.current_url:
            login_page = LoginPage(self.webdriver)
            login_page.login_webif(username, self.root_passvoid, database_name)
            self.webdriver.get(self.url + path)

    def goto_url_and_wait_until_loaded(self, path):
        self.webdriver.get(self.url + path)
        BasePage(self.webdriver).wait_for_ajax()

    def setup_test_suite(self):
        """prepare to run test cases"""
        self.go_to_index_page()

    def tear_down_test_suite(self):
        """clean up after test suite"""
        self.webdriver.delete_all_cookies()

    def teardown_testcase(self):
        """clean up after test case"""
        self.truncate_browser_log()

    def progress(self, arg):
        """state print todo"""
        print(arg)

    def add_crash_data_to_report(self):
        self.take_screenshot()
        self.save_browser_console_log()

    def truncate_browser_log(self):
        """truncate browser console log"""
        self.webdriver.get_log("browser")

    def save_browser_console_log(self):
        """attach browser console log to the allure report"""
        log_entries = self.webdriver.get_log("browser")
        if len(log_entries) > 0:
            table = BeautifulTable(maxwidth=160)
            table.columns.header = ["Level", "Source", "Timestamp", "Message"]
            for entry in log_entries:
                table.rows.append([entry["level"], entry["source"], entry["timestamp"], entry["message"]])
            attach_table(table, "Browser console log")
        else:
            attach("", "Browser console log is empty")

    def take_screenshot(self):
        """*snap*"""
        filename = datetime.now().strftime("%d-%m-%Y_%H:%M:%S.%f") + ".png"
        self.progress("Taking screenshot from: %s " % self.webdriver.current_url)
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
        self.progress("Saving screenshot to file: %s" % filename)
        attach(screenshot, name="Screenshot ({fn})".format(fn=filename), attachment_type=AttachmentType.PNG)

    def check_version(self, expected_version: VersionInfo, is_enterprise: bool):
        """validate the version displayed in the UI"""
        ver = NavigationBarPage(self.webdriver).detect_version()
        self.progress(" %s ~= %s?" % (ver["version"].lower(), str(expected_version).lower()))
        assert ver["version"].lower().lower().startswith(str(expected_version)), (
            "UI-Test: wrong version: '" + str(ver["version"]).lower() + "' vs '" + str(expected_version).lower() + "'"
        )
        if is_enterprise:
            assert ver["enterprise"] == "ENTERPRISE EDITION", "UI-Test: expected enterprise"
        else:
            assert ver["enterprise"] == "COMMUNITY EDITION", "UI-Test: expected community"